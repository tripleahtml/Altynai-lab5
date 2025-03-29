import requests
from datetime import datetime, timedelta


class AtaixTradingBot:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.ataix.kz/api"
        self.symbols_cache = None
        self.last_cache_time = 0
        self.cache_expiry = timedelta(minutes=5)

    def _make_request(self, method, endpoint, payload=None):
        """Жалпы API сұрау функциясы"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response:
                error_msg += f" | API Response: {e.response.text}"
            print(f"API қатесі ({method} {endpoint}): {error_msg}")
            return None

    def get_usdt_balance(self):
        """USDT балансын алу"""
        data = self._make_request("GET", "user/balances/USDT")
        if data and 'result' in data:
            return float(data['result']['available'])
        return None

    def get_symbol_info(self, symbol_pair):
        """Таңба жұбы туралы толық ақпарат (кешпен)"""
        if not self.symbols_cache or datetime.now() - self.last_cache_time > self.cache_expiry:
            data = self._make_request("GET", "symbols")
            if data and 'result' in data:
                self.symbols_cache = data['result']
                self.last_cache_time = datetime.now()

        if self.symbols_cache:
            for symbol in self.symbols_cache:
                if symbol.get('symbol') == symbol_pair:
                    return {
                        'ask': float(symbol.get('ask', 0)),
                        'bid': float(symbol.get('bid', 0)),
                        'min_quantity': float(symbol.get('minTradeSize', 0)),
                        'price_precision': int(symbol.get('pricePrecision', 2))
                    }
        return None

    def get_current_ask(self, symbol_pair):
        """Ағымдағы ASK бағасын алу"""
        info = self.get_symbol_info(symbol_pair)
        return info['ask'] if info else None

    def create_limit_order(self, symbol_pair, quantity, target_price_percent=None):
        """
        Limit ордер жасау
        :param symbol_pair: Таңба жұбы (мысалы 'UNI/USDT')
        :param quantity: Сатып алу көлемі (UNI)
        :param target_price_percent: ASK бағасынан төмендеу пайызы (None болса, нақты бағаны қолданады)
        """
        # Таңба ақпаратын алу
        info = self.get_symbol_info(symbol_pair)
        if not info:
            print(f"{symbol_pair} жұбы туралы ақпарат табылмады")
            return None

        # Бағаны есептеу
        current_ask = info['ask']
        if target_price_percent is not None:
            price = round(current_ask * (1 - target_price_percent / 100), info['price_precision'])
        else:
            price = round(current_ask, info['price_precision'])

        # Минималды көлемді тексеру
        if quantity < info['min_quantity']:
            print(f"Көлем тым аз. Минималды: {info['min_quantity']}")
            return None

        # Балансты тексеру
        balance = self.get_usdt_balance()
        total_cost = quantity * price
        if balance is None or balance < total_cost:
            print(f"Қаражат жеткіліксіз. Қолжетімді: {balance:.2f} USDT, Қажет: {total_cost:.2f} USDT")
            return None

        # Ордер жасау
        order = self._make_request("POST", "orders", {
            "symbol": symbol_pair,
            "side": "buy",
            "type": "limit",
            "quantity": quantity,
            "price": price,
            "subType": "gtc"
        })

        if order and order.get('status') is True:
            print(f"\nОрдер сәтті жасалды!")
            print(f"Жұп: {symbol_pair}")
            print(f"Көлем: {quantity} UNI")
            print(f"Баға: {price} USDT")
            print(f"Жалпы құны: {total_cost:.2f} USDT")
            print(f"Ордер ID: {order.get('id', 'Белгісіз')}")
            return order
        else:
            error = order.get('message', 'Белгісіз қате') if order else 'API жауап жоқ'
            print(f"\nОрдер сәтсіз: {error}")
            return None


# Қолдану мысалы
if __name__ == "__main__":
    API_KEY = "jMO7HnaoAPg2i6DJIujrPf4al10xIfJbkqyWjmVrGwCA3jNPRs9bxfsJlZlYdHc6RZfFPYRK77MBqcQjtvQ1H1"
    bot = AtaixTradingBot(API_KEY)

    # 1. Балансты көрсету
    balance = bot.get_usdt_balance()
    if balance is not None:
        print(f"Қолжетімді USDT балансы: {balance:.2f} USDT")

    # 2. Ағымдағы UNI/USDT бағасы
    symbol = "UNI/USDT"
    current_ask = bot.get_current_ask(symbol)
    if current_ask:
        print(f"\nАғымдағы {symbol} бағасы:")
        print(f"ASK: {current_ask:.4f} USDT")

        # 3. Ордер жасау (5.6 USDT бағасымен)
        print("\nОрдерді жасау...")
        order_result = bot.create_limit_order(
            symbol_pair=symbol,
            quantity=0.01,  # 0.01 UNI
            target_price_percent=None  # Нақты 5.6 USDT бағасын қолдану
        )

        if not order_result:
            # Егер ордер сәтсіз болса, ағымдағы бағадан 8% төмен бағаны ұсыну
            suggested_price = round(current_ask * 0.92, 3)
            print(f"\nҰсыныс: Бағаны {suggested_price} деңгейіне түсіріп көріңіз")

            # Ұсынылған бағамен қайта жасау
            retry_order = bot.create_limit_order(
                symbol_pair=symbol,
                quantity=0.01,
                target_price_percent=8  # 8% төмен
            )
    else:
        print(f"\n{symbol} жұбы туралы ақпарат алу мүмкін болмады")