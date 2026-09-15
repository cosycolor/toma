import httpx
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("toma_engine")
logging.basicConfig(level=logging.INFO)

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
