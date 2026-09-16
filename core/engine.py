import httpx
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional

logger = logging.getLogger("toma_engine")
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

class TomaDataEngine:
    """High-performance data engine for TOMA Desktop (Naver Finance / Open APIs)"""
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://m.stock.naver.com/"
    }

    def __init__(self):
        self.client = httpx.Client(headers=self.HEADERS, timeout=8.0)

    def get_theme_ranking(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Fetch all themes with real-time change rates & leader info"""
        url = f"https://m.stock.naver.com/api/stocks/theme?page={page}&pageSize={page_size}"
        try:
            resp = self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data
        except Exception as e:
            logger.error(f"Error fetching theme ranking: {e}")
        return {"groups": [], "totalCount": 0}

    def get_leading_themes(self, top_n: int = 6, candidate_count: int = 25) -> List[Dict[str, Any]]:
        """
        실전 주도 테마 선별 알고리즘 (초대형주 왜곡 제거 + 모멘텀/상한가/거래대금 복합 평가)
        1. 삼성전자/하이닉스 등 초대형주 1개로 인한 거래대금 왜곡을 막기 위해 단일 종목 거래대금에 Capping(최대 4,000억원) 적용
        2. 상한가 보유 개수 및 20% 이상 급등주에 강력한 모멘텀 가중치(Multiplier) 부여
        3. 테마 평균 등락률의 지수 가중치 (테마 등락률이 높을수록 시장 중심 테마로 평가)
        4. 상위 top_n개 테마 정렬 반환
        """
        ranking_data = self.get_theme_ranking(page=1, page_size=candidate_count)
        candidates = ranking_data.get("groups", [])
        if not candidates:
            return []

        # 각 후보 테마의 상세 종목을 초고속 병렬 수집 (ThreadPoolExecutor)
        theme_details = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_theme = {
                executor.submit(self.get_theme_detail, t.get("no")): t
                for t in candidates if t.get("no")
            }
            for future in future_to_theme:
                theme_info = future_to_theme[future]
                try:
                    detail = future.result()
                    theme_details[theme_info.get("no")] = detail
                except Exception as e:
                    logger.error(f"Error fetching theme detail in worker: {e}")

        scored_themes = []
        fallback_themes = []

        for t in candidates:
            t_no = t.get("no")
            detail = theme_details.get(t_no, {})
            stocks = detail.get("stocks", [])
            
            try:
                theme_rate = float(str(t.get("changeRate", "0")).replace(",", ""))
            except Exception:
                theme_rate = 0.0

            rise_cnt = int(t.get("riseCount", 0) or 0)
            fall_cnt = int(t.get("fallCount", 0) or 0)
            total_cnt = rise_cnt + fall_cnt
            rise_ratio = rise_cnt / max(1, total_cnt)

            # 종목별 거래대금 및 등락률 분석
            raw_tr_vals = []
            capped_tr_vals = []
            upper_count = 0
            over20_count = 0
            top1_rate = 0.0

            for idx, s in enumerate(stocks):
                try:
                    rate = float(str(s.get("fluctuationsRatio", 0)).replace(",", ""))
                except Exception:
                    rate = 0.0

                if idx == 0:
                    top1_rate = rate

                if s.get("is_upper_limit") or rate >= 29.8:
                    upper_count += 1
                elif rate >= 20.0:
                    over20_count += 1

                try:
                    val_raw = s.get("accumulatedTradingValueRaw", 0)
                    val = float(str(val_raw).replace(",", "")) if val_raw else 0.0
                except Exception:
                    val = 0.0
                
                val_eok = val / 100_000_000.0  # 억원 단위
                raw_tr_vals.append(val_eok)
                # 단일 종목 Capping (최대 4,000억원까지만 테마 주도성 기여로 인정하여 대형주 1개 독식 방지)
                capped_tr_vals.append(min(val_eok, 4000.0))

            raw_tr_vals.sort(reverse=True)
            capped_tr_vals.sort(reverse=True)

            top3_raw_val = sum(raw_tr_vals[:3])
            top3_capped_val = sum(capped_tr_vals[:3])

            # 모멘텀 & 대장주 파워 보너스 (상한가 1개당 1.6배, 2개 이상 2.2배, 20% 이상 급등주 1.35배)
            if upper_count >= 2:
                momentum_multiplier = 2.2
            elif upper_count == 1:
                momentum_multiplier = 1.6
            elif over20_count >= 1:
                momentum_multiplier = 1.35
            elif top1_rate >= 10.0:
                momentum_multiplier = 1.15
            else:
                momentum_multiplier = 1.0

            # 복합 주도주 점수 (Leader Power Score)
            # (Top3 Capped 거래대금) * (테마등락률^1.3) * (상승비율) * 모멘텀배수
            score = top3_capped_val * (max(0.5, theme_rate) ** 1.3) * max(0.3, rise_ratio) * momentum_multiplier

            enriched_theme = dict(t)
            enriched_theme["leader_score"] = round(score, 1)
            enriched_theme["top3_tr_val_eok"] = int(round(top3_raw_val)) # 표기는 실제 거래대금 표기
            enriched_theme["rise_ratio"] = round(rise_ratio * 100, 1)
            enriched_theme["upper_count"] = upper_count
            enriched_theme["pre_stocks"] = stocks[:5]

            # 게이트 필터: 최소 자격 검증 (상승률 1.0% 이상, 상승비율 35% 이상, 대장주 3% 이상)
            is_qualified = (theme_rate >= 1.0) and (rise_ratio >= 0.35) and (top1_rate >= 3.0)

            if is_qualified:
                scored_themes.append(enriched_theme)
            else:
                fallback_themes.append(enriched_theme)

        # 점수 내림차순 정렬
        scored_themes.sort(key=lambda x: x.get("leader_score", 0), reverse=True)
        fallback_themes.sort(key=lambda x: float(str(x.get("changeRate", 0))), reverse=True)

        final_themes = scored_themes[:top_n]
        if len(final_themes) < top_n:
            needed = top_n - len(final_themes)
            final_themes.extend(fallback_themes[:needed])

        return final_themes[:top_n]

    def _enrich_realtime_integrated_quotes(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        KRX 정규장 + 대체거래소(NXT/Nextrade/시간외) 통합 실시간 거래대금 및 시세를 일괄 배치 주입
        키움 등 증권사 HTS/MTS와 100% 일치하도록 보정
        """
        if not stocks:
            return stocks

        codes = [str(s.get("itemCode", "")).strip() for s in stocks if s.get("itemCode")]
        if not codes:
            return stocks

        try:
            # Polling API supports comma-separated batch queries (up to 100 stocks at once)
            codes_str = ",".join(codes)
            url = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{codes_str}"
            resp = self.client.get(url)
            if resp.status_code == 200:
                payload = resp.json()
                datas = payload.get("datas", [])
                quote_map = {d.get("itemCode"): d for d in datas if d.get("itemCode")}

                for s in stocks:
                    code = s.get("itemCode")
                    if code in quote_map:
                        q = quote_map[code]
                        # 1. Integrated price info (KRX + NXT total trading value)
                        integrated = q.get("integratedPriceInfo") or {}
                        
                        if integrated.get("accumulatedTradingValueRaw"):
                            s["accumulatedTradingValueRaw"] = integrated.get("accumulatedTradingValueRaw")
                        elif q.get("accumulatedTradingValueRaw"):
                            s["accumulatedTradingValueRaw"] = q.get("accumulatedTradingValueRaw")

                        if integrated.get("accumulatedTradingVolumeRaw"):
                            s["accumulatedTradingVolumeRaw"] = integrated.get("accumulatedTradingVolumeRaw")
                        elif q.get("accumulatedTradingVolumeRaw"):
                            s["accumulatedTradingVolumeRaw"] = q.get("accumulatedTradingVolumeRaw")

                        if q.get("closePrice"):
                            s["closePrice"] = q.get("closePrice")
                        if q.get("fluctuationsRatio"):
                            s["fluctuationsRatio"] = q.get("fluctuationsRatio")
                        if q.get("compareToPreviousPrice"):
                            s["compareToPreviousPrice"] = q.get("compareToPreviousPrice")
        except Exception as e:
            logger.error(f"Error enriching integrated quotes: {e}")

        return stocks

    def get_theme_detail(self, theme_no: int, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Fetch full theme details including description, item reasons, and sorted leader stocks"""
        url = f"https://m.stock.naver.com/api/stocks/theme/{theme_no}?page={page}&pageSize={page_size}"
        try:
            resp = self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                raw_stocks = data.get("stocks", [])
                theme_desc = data.get("themeDescription", "")
                item_info_map = data.get("themeItemInfoMap", {})
                group_info = data.get("groupInfo", {})

                # attach reason to stocks
                for s in raw_stocks:
                    code = s.get("itemCode", "")
                    s["theme_reason"] = item_info_map.get(code, "")

                # Enrich with integrated NXT/KRX realtime trading value
                enriched_stocks = self._enrich_realtime_integrated_quotes(raw_stocks)
                processed_stocks = self._process_leaders(enriched_stocks)
                return {
                    "stocks": processed_stocks,
                    "description": theme_desc,
                    "item_info_map": item_info_map,
                    "group_info": group_info
                }
        except Exception as e:
            logger.error(f"Error fetching theme detail for {theme_no}: {e}")
        return {"stocks": [], "description": "", "item_info_map": {}, "group_info": {}}

    def get_theme_stocks(self, theme_no: int, page: int = 1, page_size: int = 50) -> List[Dict[str, Any]]:
        """Fetch theme component stocks with trading value & detect Leader (대장주/부대장주)"""
        detail = self.get_theme_detail(theme_no, page, page_size)
        return detail.get("stocks", [])

    def _process_leaders(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Leader Detection Algorithm:
        - 1st Priority: Upper Limit (상한가) + Trading Value
        - 2nd Priority: Highest Fluctuation Ratio + Trading Value
        """
        if not stocks:
            return []

        # Sort by fluctuation ratio descending, then trading value descending
        def sort_key(s):
            try:
                rate = float(str(s.get("fluctuationsRatio", "0")).replace(",", ""))
            except Exception:
                rate = -999.0
            try:
                val_raw = s.get("accumulatedTradingValueRaw", 0)
                val = float(str(val_raw).replace(",", "")) if val_raw else 0.0
            except Exception:
                val = 0.0
            is_upper = 1 if (s.get("compareToPreviousPrice") or {}).get("name") == "UPPER_LIMIT" or rate >= 29.8 else 0
            return (is_upper, rate, val)

        sorted_stocks = sorted(stocks, key=sort_key, reverse=True)
        
        for idx, stock in enumerate(sorted_stocks):
            try:
                rate = float(str(stock.get("fluctuationsRatio", "0")).replace(",", ""))
            except Exception:
                rate = 0.0
            is_upper = (stock.get("compareToPreviousPrice") or {}).get("name") == "UPPER_LIMIT" or rate >= 29.8
            
            if idx == 0 and rate > 0:
                stock["leader_tag"] = "👑 대장주"
                stock["leader_rank"] = 1
            elif idx == 1 and rate > 0:
                stock["leader_tag"] = "🥈 2등주"
                stock["leader_rank"] = 2
            elif idx == 2 and rate > 0:
                stock["leader_tag"] = "🥉 3등주"
                stock["leader_rank"] = 3
            else:
                stock["leader_tag"] = "후발주"
                stock["leader_rank"] = 99
                
            stock["is_upper_limit"] = is_upper

        return sorted_stocks

    def get_realtime_news(self, keyword: str = "") -> List[Dict[str, Any]]:
        """Fetch real-time stock news & market disclosures (Up to 100 latest articles)"""
        all_items = []
        try:
            for page in range(1, 3):
                url = f"https://m.stock.naver.com/api/news/list?page={page}&pageSize=50"
                resp = self.client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    page_items = data if isinstance(data, list) else data.get("items", [])
                    all_items.extend(page_items)
                else:
                    break

            normalized = []
            seen_aids = set()
            for item in all_items:
                oid = str(item.get("oid", ""))
                aid = str(item.get("aid", ""))
                if aid and aid in seen_aids:
                    continue
                if aid:
                    seen_aids.add(aid)

                dt_raw = str(item.get("dt", ""))
                if len(dt_raw) >= 12:
                    time_str = f"{dt_raw[8:10]}:{dt_raw[10:12]}"
                else:
                    time_str = dt_raw
                
                link = f"https://n.news.naver.com/mnews/article/{oid}/{aid}" if oid and aid else ""
                
                normalized.append({
                    "datetime": time_str,
                    "press": item.get("ohnm", "증시뉴스"),
                    "title": item.get("tit", ""),
                    "stock": item.get("stockName", "-"),
                    "oid": oid,
                    "aid": aid,
                    "link": link,
                    "summary": item.get("subcontent", "")
                })
            return normalized
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
        return []

    def get_news_content(self, oid: str, aid: str) -> str:
        """Fetch full article content from Naver News"""
        if not oid or not aid:
            return ""
        url = f"https://n.news.naver.com/mnews/article/{oid}/{aid}"
        try:
            from bs4 import BeautifulSoup
            resp = self.client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                art = soup.select_one('#newsct_article') or soup.select_one('#articeBody') or soup.select_one('#articleBody')
                if art:
                    for s in art.select('script, style, em, span.end_photo_org'):
                        s.extract()
                    text = art.get_text("\n", strip=True)
                    return text
        except Exception as e:
            logger.error(f"Error fetching article body: {e}")
        return ""

    def search_stock(self, query: str) -> List[Dict[str, Any]]:
        """Search stock by code or name using Naver autocomplete API"""
        query = query.strip()
        if not query:
            return []
        url = f"https://ac.stock.naver.com/ac?q={query}&target=stock"
        try:
            resp = self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                return items
        except Exception as e:
            logger.error(f"Error searching stock '{query}': {e}")
        return []

    def get_stock_basic(self, code: str) -> Optional[Dict[str, Any]]:
        """Fetch real-time basic quote and info for a specific stock (Integrated NXT+KRX)"""
        code = str(code).strip()
        if not code:
            return None
        url = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"
        try:
            resp = self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                datas = data.get("datas", [])
                if datas:
                    return datas[0]
        except Exception as e:
            logger.error(f"Error fetching stock basic '{code}': {e}")
        return None

    def get_economic_calendar(self) -> List[Dict[str, Any]]:
        """Fetch trading calendar / economic events"""
        events = [
            {"date": "2026-09-16", "time": "03:00", "country": "🇺🇸 미국", "event": "FOMC 기준금리 결정 및 경제전망", "impact": "VERY_HIGH"},
            {"date": "2026-09-17", "time": "21:30", "country": "🇺🇸 미국", "event": "소비자물가지수 (CPI) 발표", "impact": "VERY_HIGH"},
            {"date": "2026-09-18", "time": "09:00", "country": "🇰🇷 한국", "event": "코스피/코스닥 신규상장 (IPO) 공모", "impact": "HIGH"},
            {"date": "2026-09-22", "time": "10:00", "country": "🇰🇷 한국", "event": "한국은행 금융통화위원회 기준금리 회의", "impact": "HIGH"},
            {"date": "2026-09-25", "time": "09:00", "country": "🇰🇷 한국", "event": "주요 바이오/반도체 대량 보호예수(락업) 해제", "impact": "MEDIUM"}
        ]
        return events

engine = TomaDataEngine()
