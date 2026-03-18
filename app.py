import streamlit as st
import pandas as pd
import yfinance as yf
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ==========================================
# 0. 종목 한글명 매핑 딕셔너리
# ==========================================
TICKER_NAMES = {
    # 미국 주식
    'AAPL':  '애플',
    'MSFT':  '마이크로소프트',
    'GOOGL': '구글(알파벳)',
    'AMZN':  '아마존',
    'NVDA':  '엔비디아',
    'TSLA':  '테슬라',
    'META':  '메타(페이스북)',
    'NFLX':  '넷플릭스',
    'AMD':   'AMD',
    'INTC':  '인텔',
    'DIS':   '디즈니',
    'SBUX':  '스타벅스',
    'NKE':   '나이키',
    'KO':    '코카콜라',
    'PEP':   '펩시',
    'MCD':   '맥도날드',
    'WMT':   '월마트',
    'BA':    '보잉',
    'JPM':   'JP모건',
    'V':     '비자',
    'GME':   '게임스탑',
    'AMC':   'AMC엔터테인먼트',
    'PLTR':  '팔란티어',
    'COIN':  '코인베이스',
    'RBLX':  '로블록스',
    'UBER':  '우버',
    'ABNB':  '에어비앤비',
    'PFE':   '화이자',
    'MRNA':  '모더나',
    'MA':    '마스터카드',
    # 한국 주식
    '005930.KS': '삼성전자',
    '000660.KS': 'SK하이닉스',
    '373220.KS': 'LG에너지솔루션',
    '207940.KS': '삼성바이오로직스',
    '005380.KS': '현대차',
    '035420.KS': 'NAVER',
    '035720.KS': '카카오',
    '051910.KS': 'LG화학',
    '000270.KS': '기아',
    '068270.KS': '셀트리온',
    '005490.KS': 'POSCO홀딩스',
    '105560.KS': 'KB금융',
    '028260.KS': '삼성물산',
    '012330.KS': '현대모비스',
    '066570.KS': 'LG전자',
    '036570.KS': 'NC소프트',
    '259960.KS': '크래프톤',
    '352820.KS': '하이브',
    '011200.KS': 'HMM(현대상선)',
    '096770.KS': 'SK이노베이션',
    '034730.KS': 'SK(주)',
    '010130.KS': '고려아연',
    '316140.KS': '우리금융',
    '024110.KS': '기업은행',
    '032830.KS': '삼성생명',
    '090430.KS': '아모레퍼시픽',
    '009150.KS': '삼성전기',
    '042700.KS': '한미반도체',
    '010950.KS': 'S-Oil',
    '018260.KS': '삼성SDS',
}

def ticker_label(ticker: str) -> str:
    """selectbox에 표시할 한글명 + 티커 문자열 반환"""
    name = TICKER_NAMES.get(ticker, ticker)
    return f"{name} ({ticker})"


# ==========================================
# 1. 실제 역사 뉴스 생성 (Anthropic API)
# ==========================================
@st.cache_data(ttl=86400, show_spinner=False)
def fetch_historical_news(year_month_label: str, api_key: str) -> str:
    """
    year_month_label 예: '2024년 1월'
    퀴즈 정답 시 호출 — 해당 월의 실제 경제 이슈 5가지를 반환.
    결과는 하루 동안 캐시됨(같은 날짜·API키 조합 재호출 방지).
    """
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        prompt = (
            f"당신은 경제·금융 전문 애널리스트입니다.\n"
            f"'{year_month_label}'에 실제로 있었던 주요 경제·금융 이슈를 5가지 알려주세요.\n"
            f"투자자가 다음 달 주식 투자 전략을 세우는 데 도움이 되도록,\n"
            f"미국 증시와 한국 증시 이슈를 균형 있게, 실제 사건 기반으로 작성하세요.\n"
            f"각 항목은 📌 이모지로 시작하고 한 줄로만 작성하세요."
        )
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except Exception as e:
        return f"⚠️ 뉴스 로딩 실패: {e}\n(API 키를 확인하거나 사이드바에서 다시 입력해주세요)"


# ==========================================
# 2. 팀 및 자산 관리 클래스
# ==========================================
class Team:
    def __init__(self, name):
        self.name = name
        self.usd_balance = 100000.0
        self.krw_balance = 100000000.0
        self.portfolio = {}
        self.is_bankrupt = False

    def get_total_value_krw(self, get_price_func, current_date):
        if self.is_bankrupt:
            return 0
        exchange_rate = get_price_func('USDKRW=X', current_date)
        if exchange_rate == 0:
            exchange_rate = 1300
        total_value = self.krw_balance + (self.usd_balance * exchange_rate)
        for ticker, info in self.portfolio.items():
            price = get_price_func(ticker, current_date)
            shares = info['shares']
            if ticker.endswith('.KS'):
                total_value += price * shares
            else:
                total_value += (price * shares) * exchange_rate
        return total_value


# ==========================================
# 3. 게임 시스템 및 로직 클래스
# ==========================================
class MockInvestmentGame:
    def __init__(self, team_names, total_turns=12, start_date_choice='random'):
        self.total_turns = total_turns
        self.current_turn = 1
        self.teams = [Team(name) for name in team_names]

        self.start_dates_pool = [
            '2001-01-01', '2005-05-01', '2010-01-01',
            '2015-05-01', '2020-01-01', '2023-01-01'
        ]
        chosen_date = (
            start_date_choice
            if start_date_choice in self.start_dates_pool
            else random.choice(self.start_dates_pool)
        )
        self.current_date = datetime.strptime(chosen_date, '%Y-%m-%d')

        self.us_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX', 'AMD', 'INTC',
            'DIS', 'SBUX', 'NKE', 'KO', 'PEP', 'MCD', 'WMT', 'BA', 'JPM', 'V',
            'GME', 'AMC', 'PLTR', 'COIN', 'RBLX', 'UBER', 'ABNB', 'PFE', 'MRNA', 'MA'
        ]
        self.kr_tickers = [
            '005930.KS', '000660.KS', '373220.KS', '207940.KS', '005380.KS',
            '035420.KS', '035720.KS', '051910.KS', '000270.KS', '068270.KS',
            '005490.KS', '105560.KS', '028260.KS', '012330.KS', '066570.KS',
            '036570.KS', '259960.KS', '352820.KS', '011200.KS', '096770.KS',
            '034730.KS', '010130.KS', '316140.KS', '024110.KS', '032830.KS',
            '090430.KS', '009150.KS', '042700.KS', '010950.KS', '018260.KS'
        ]
        self.tradeable_tickers = self.us_tickers + self.kr_tickers
        self.all_tickers = self.tradeable_tickers + ['USDKRW=X']
        self.market_data = pd.DataFrame()

        self.quizzes = [
            {"question": "선택으로 인해 포기해야 하는 대안 중 가장 가치 있는 것은?", "options": ["1. 매몰비용", "2. 기회비용", "3. 한계비용"], "answer": 2},
            {"question": "사람들의 욕망은 무한하지만, 자원은 한정되어 있는 상태는?", "options": ["1. 희소성", "2. 효율성", "3. 형평성"], "answer": 1},
            {"question": "다른 조건이 같을 때, 가격이 오르면 그 상품의 수요량은 어떻게 될까요?", "options": ["1. 증가한다", "2. 감소한다", "3. 변동 없다"], "answer": 2},
            {"question": "콜라와 사이다처럼 한 재화의 가격이 오를 때 다른 재화의 수요가 증가하는 관계는?", "options": ["1. 보완재", "2. 정상재", "3. 대체재"], "answer": 3},
            {"question": "스마트폰과 충전기처럼 함께 소비할 때 만족감이 커지는 재화는?", "options": ["1. 보완재", "2. 대체재", "3. 열등재"], "answer": 1},
            {"question": "시장에서 수요량과 공급량이 일치하여 결정되는 가격은?", "options": ["1. 최고가격", "2. 균형가격", "3. 최저가격"], "answer": 2},
            {"question": "물가가 지속적으로 오르고 화폐 가치가 떨어지는 현상은?", "options": ["1. 디플레이션", "2. 스태그플레이션", "3. 인플레이션"], "answer": 3},
            {"question": "인플레이션이 발생했을 때 일반적으로 더 유리해지는 사람은?", "options": ["1. 현금 보유자", "2. 돈을 빌린 사람", "3. 돈을 빌려준 사람"], "answer": 2},
            {"question": "물가가 지속적으로 하락하며 경제 활동이 침체되는 현상은?", "options": ["1. 인플레이션", "2. 디플레이션", "3. 리디노미네이션"], "answer": 2},
            {"question": "중앙은행이 물가를 안정시키기 위해 시중 통화량을 줄이려 할 때 취할 행동은?", "options": ["1. 기준금리 인상", "2. 기준금리 인하", "3. 세금 감면"], "answer": 1},
            {"question": "외국 화폐에 대한 자국 화폐의 교환 비율은?", "options": ["1. 금리", "2. 물가", "3. 환율"], "answer": 3},
            {"question": "원/달러 환율이 올랐습니다. 이때 웃게 되는 사람은?", "options": ["1. 해외 여행객", "2. 수입업자", "3. 수출업자"], "answer": 3},
            {"question": "원/달러 환율이 떨어졌습니다. 이때 피해를 볼 가능성이 큰 사람은?", "options": ["1. 유학생 부모", "2. 부품 수입 기업", "3. 수출 기업"], "answer": 3},
            {"question": "일정 기간 한 나라 안에서 새로 생산된 최종 생산물의 가치 합은?", "options": ["1. 물가지수", "2. 국내총생산(GDP)", "3. 국민총소득(GNI)"], "answer": 2},
            {"question": "소득이 많은 사람에게 더 높은 비율의 세금을 거두는 제도는?", "options": ["1. 비례세", "2. 누진세", "3. 역진세"], "answer": 2},
            {"question": "납세자와 담세자가 다른 세금은?", "options": ["1. 간접세", "2. 직접세", "3. 소득세"], "answer": 1},
            {"question": "한 기업이 시장을 장악하여 가격을 마음대로 결정할 수 있는 시장은?", "options": ["1. 완전경쟁시장", "2. 독점시장", "3. 과점시장"], "answer": 2},
            {"question": "소수의 기업이 시장을 지배하며 눈치를 보며 경쟁하는 시장은?", "options": ["1. 독점시장", "2. 과점시장", "3. 완전경쟁시장"], "answer": 2},
            {"question": "어떤 활동이 타인에게 의도치 않은 혜택을 주는데도 대가를 받지 못하는 상황은?", "options": ["1. 긍정적 외부효과", "2. 부정적 외부효과", "3. 무임승차"], "answer": 1},
            {"question": "국방 서비스처럼 돈을 내지 않은 사람도 이용할 수 있는 재화는?", "options": ["1. 사유재", "2. 공공재", "3. 대체재"], "answer": 2},
            {"question": "더 적은 기회비용으로 생산할 수 있는 상품에 집중하는 원리는?", "options": ["1. 절대우위", "2. 보호무역", "3. 비교우위"], "answer": 3},
            {"question": "자국 산업을 보호하기 위해 수입품에 높은 관세를 매기는 정책은?", "options": ["1. 자유무역", "2. 보호무역", "3. 공정무역"], "answer": 2},
            {"question": "원금뿐만 아니라 원금에서 생겨난 이자에도 이자가 붙는 계산 방식은?", "options": ["1. 단리", "2. 복리", "3. 마이너스 금리"], "answer": 2},
            {"question": "회사가 이익을 내서 그 이익의 일부를 주주들에게 나누어 주는 돈은?", "options": ["1. 이자", "2. 배당금", "3. 세금"], "answer": 2},
            {"question": "호황기를 지나 침체기로 접어드는 등 경제 상태가 변하는 것은?", "options": ["1. 경제성장", "2. 경기변동", "3. 인플레이션"], "answer": 2},
            {"question": "직장을 구하려는 의지가 있음에도 일자리를 구하지 못한 상태는?", "options": ["1. 고용", "2. 실업", "3. 은퇴"], "answer": 2},
            {"question": "개인이나 기업이 발명, 상표 등에 대해 가지는 독점적인 권리는?", "options": ["1. 소유권", "2. 지적재산권", "3. 영업권"], "answer": 2},
            {"question": "시장에서 가격이 수요와 공급을 조절하는 기능을 빗댄 애덤 스미스의 말은?", "options": ["1. 보이지 않는 손", "2. 보이는 손", "3. 황금 손"], "answer": 1},
            {"question": "가계가 노동이나 자본을 제공하고 얻는 대가는?", "options": ["1. 지출", "2. 소득", "3. 부채"], "answer": 2},
            {"question": "일반적으로 예금 금리와 대출 금리 중 어느 것이 더 높을까요?", "options": ["1. 예금 금리", "2. 대출 금리", "3. 항상 같다"], "answer": 2},
            {"question": "정부가 경제를 살리기 위해 세금을 줄이고 지출을 늘리는 정책은?", "options": ["1. 긴축 재정", "2. 확대 재정", "3. 통화 정책"], "answer": 2},
            {"question": "앞으로 주가가 오를 것으로 기대하는 상승장을 상징하는 동물은?", "options": ["1. 곰(Bear)", "2. 황소(Bull)", "3. 독수리(Eagle)"], "answer": 2},
            {"question": "앞으로 주가가 떨어질 것으로 예상하는 하락장을 상징하는 동물은?", "options": ["1. 곰(Bear)", "2. 황소(Bull)", "3. 사자(Lion)"], "answer": 1},
            {"question": "기업이 새로 주식을 발행하여 사람들에게 처음으로 파는 과정을 뜻하는 약자는?", "options": ["1. GDP", "2. IPO", "3. M&A"], "answer": 2},
            {"question": "두 개 이상의 기업이 하나로 합쳐지거나 다른 기업을 사들이는 것을 뜻하는 약자는?", "options": ["1. M&A", "2. IPO", "3. CEO"], "answer": 1},
        ]
        random.shuffle(self.quizzes)

    def load_market_data(self):
        end_date = self.current_date + relativedelta(months=self.total_turns + 2)
        raw = yf.download(
            self.all_tickers,
            start=self.current_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            progress=False,
            auto_adjust=True
        )
        if isinstance(raw.columns, pd.MultiIndex):
            level0 = raw.columns.get_level_values(0)
            if 'Close' in level0:
                self.market_data = raw['Close']
            elif 'Price' in level0:
                self.market_data = raw['Price']
            else:
                self.market_data = raw[level0[0]]
        else:
            self.market_data = raw

        if hasattr(self.market_data.index, 'tz') and self.market_data.index.tz is not None:
            self.market_data.index = self.market_data.index.tz_localize(None)

    def get_price(self, ticker, date):
        if self.market_data.empty:
            return 0.0
        try:
            subset = self.market_data.loc[date.strftime('%Y-%m-%d'):]
            if not subset.empty and ticker in subset.columns:
                valid = subset[ticker].dropna()
                if not valid.empty:
                    return float(valid.iloc[0])
        except (KeyError, TypeError):
            pass
        return 0.0

    def buy_stock(self, team, ticker, shares):
        price = self.get_price(ticker, self.current_date)
        if price == 0:
            return False, "현재 거래할 수 없는 주식입니다."
        is_kr = ticker.endswith('.KS')
        required = price * shares
        balance = team.krw_balance if is_kr else team.usd_balance
        if balance >= required:
            if is_kr:
                team.krw_balance -= required
            else:
                team.usd_balance -= required
            if ticker in team.portfolio:
                old_s = team.portfolio[ticker]['shares']
                old_a = team.portfolio[ticker]['avg_price']
                new_s = old_s + shares
                team.portfolio[ticker] = {
                    'shares': new_s,
                    'avg_price': ((old_s * old_a) + (shares * price)) / new_s
                }
            else:
                team.portfolio[ticker] = {'shares': shares, 'avg_price': price}
            return True, f"[{team.name}] {ticker_label(ticker)} {shares}주 매수 완료!"
        return False, f"[{team.name}] 잔고가 부족합니다."

    def sell_stock(self, team, ticker, shares):
        if ticker not in team.portfolio or team.portfolio[ticker]['shares'] < shares:
            return False, f"[{team.name}] 보유 수량이 부족합니다."
        price = self.get_price(ticker, self.current_date)
        is_kr = ticker.endswith('.KS')
        revenue = price * shares
        team.portfolio[ticker]['shares'] -= shares
        if team.portfolio[ticker]['shares'] == 0:
            del team.portfolio[ticker]
        if is_kr:
            team.krw_balance += revenue
        else:
            team.usd_balance += revenue
        return True, f"[{team.name}] {ticker_label(ticker)} {shares}주 매도 완료!"

    def exchange_currency(self, team, direction, amount_usd):
        rate = self.get_price('USDKRW=X', self.current_date)
        if rate == 0:
            rate = 1300.0
        if direction == 'KRW_TO_USD':
            applied = rate * 1.05
            required_krw = amount_usd * applied
            if team.krw_balance >= required_krw:
                team.krw_balance -= required_krw
                team.usd_balance += amount_usd
                return True, f"{amount_usd:,.0f}달러 구매 완료 (적용환율: {applied:,.2f}원/달러)"
            return False, "원화 잔고가 부족합니다."
        elif direction == 'USD_TO_KRW':
            applied = rate * 0.95
            received = amount_usd * applied
            if team.usd_balance >= amount_usd:
                team.usd_balance -= amount_usd
                team.krw_balance += received
                return True, f"{received:,.0f}원 획득 완료 (적용환율: {applied:,.2f}원/달러)"
            return False, "달러 잔고가 부족합니다."

    def check_bankruptcy(self, team):
        if team.get_total_value_krw(self.get_price, self.current_date) < 23_000_000:
            team.is_bankrupt = True

    def next_turn(self):
        for team in self.teams:
            if not team.is_bankrupt:
                self.check_bankruptcy(team)
        self.current_turn += 1
        self.current_date += relativedelta(months=1)


# ==========================================
# 4. UI 헬퍼 함수
# ==========================================
def display_portfolio_ui(team, get_price_func, current_date):
    if not team.portfolio:
        st.info("현재 보유 중인 주식이 없습니다.")
        return
    rows = []
    for ticker, info in team.portfolio.items():
        shares = info['shares']
        avg_price = info['avg_price']
        cur_price = get_price_func(ticker, current_date)
        ret = ((cur_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
        currency = "KRW" if ticker.endswith('.KS') else "USD"
        rows.append({
            "종목명": ticker_label(ticker),
            "수량": shares,
            "평단가": f"{avg_price:,.0f}원" if currency == "KRW" else f"${avg_price:,.2f}",
            "현재가": f"{cur_price:,.0f}원" if currency == "KRW" else f"${cur_price:,.2f}",
            "수익률": f"{ret:+.2f}%",
        })
    df = pd.DataFrame(rows)

    def color_return(val):
        if '+' in val:
            return 'color: red'
        elif '-' in val:
            return 'color: blue'
        return 'color: black'

    try:
        styled = df.style.map(color_return, subset=['수익률'])
    except AttributeError:
        styled = df.style.applymap(color_return, subset=['수익률'])
    st.dataframe(styled, use_container_width=True, hide_index=True)


def show_exchange_rate_box(rate: float):
    """현재 환율과 매수/매도 적용 환율을 정보 박스로 표시"""
    if rate > 0:
        st.info(
            f"💱 **현재 USD/KRW 환율: {rate:,.2f} 원**  \n"
            f"달러 매수 시 적용: **{rate * 1.05:,.2f}원** (+5% 수수료)  │  "
            f"달러 매도 시 적용: **{rate * 0.95:,.2f}원** (-5% 수수료)"
        )
    else:
        st.warning("⚠️ 환율 데이터를 불러올 수 없습니다. 기본값 1,300원으로 처리됩니다.")


def make_shares_slider(label: str, team, ticker: str, game, key: str) -> int:
    """
    보유 잔고 기반으로 최대 매수 가능 수량을 계산하고
    슬라이더 step을 자동 조정해서 반환합니다.
    """
    price = game.get_price(ticker, game.current_date)
    is_kr = ticker.endswith('.KS')
    balance = team.krw_balance if is_kr else team.usd_balance

    if price > 0:
        max_buy = max(1, int(balance / price))
    else:
        max_buy = 1

    # 슬라이더 range가 너무 넓으면 step을 크게
    if max_buy >= 10000:
        step = 100
    elif max_buy >= 1000:
        step = 10
    elif max_buy >= 100:
        step = 5
    else:
        step = 1

    price_str = f"{price:,.0f}원" if is_kr else f"${price:,.2f}"
    help_txt = f"현재가 {price_str} | 최대 매수 가능: {max_buy:,}주"

    return st.slider(
        label,
        min_value=1,
        max_value=max(1, max_buy),
        value=1,
        step=step,
        key=key,
        help=help_txt,
    )


# ==========================================
# 5. Streamlit 메인 앱
# ==========================================
def main():
    st.set_page_config(page_title="글로벌 모의투자 게임", layout="wide")
    st.title("글로벌 모의투자 보드게임")

    # 사이드바: Anthropic API 키 입력
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        api_key = st.text_input(
            "Anthropic API 키 (실시간 뉴스용)",
            type="password",
            placeholder="sk-ant-...",
            help="퀴즈 정답 시 해당 월의 실제 경제 뉴스를 불러오는 데 사용됩니다."
        )
        if api_key:
            st.success("API 키 입력 완료 ✅")
        else:
            st.warning("API 키 없이는 뉴스 기능이 비활성화됩니다.")

    if 'game_started' not in st.session_state:
        st.session_state.game_started = False

    # ── 로비 화면 ────────────────────────────────────────────
    if not st.session_state.game_started:
        st.subheader("게임 세팅 로비")
        with st.form("lobby_form"):
            st.markdown("#### 1. 게임 기본 설정")
            col1, col2 = st.columns(2)
            total_turns = col1.slider("총 게임 길이 (턴/개월)", min_value=8, max_value=18, value=12)
            start_dates = ['random', '2001-01-01', '2005-05-01', '2010-01-01',
                           '2015-05-01', '2020-01-01', '2023-01-01']
            start_date_choice = col2.selectbox("시작 시점 선택", start_dates)

            st.markdown("#### 2. 참가 팀 설정")
            team_count = st.number_input("참가할 팀 수", min_value=1, max_value=4, value=2)
            team_names = [
                st.text_input(f"팀 {i+1} 이름", value=f"Team {i+1}")
                for i in range(int(team_count))
            ]

            if st.form_submit_button("게임 시작하기"):
                with st.spinner('과거 주식 데이터를 불러오는 중입니다... (최대 1~2분 소요)'):
                    st.session_state.game = MockInvestmentGame(team_names, total_turns, start_date_choice)
                    st.session_state.game.load_market_data()
                    st.session_state.game_over = False
                    st.session_state.quiz_answered = False
                    st.session_state.news_unlocked = False
                    st.session_state.current_quiz = (
                        st.session_state.game.quizzes.pop()
                        if st.session_state.game.quizzes else None
                    )
                    st.session_state.game_started = True
                st.rerun()

    # ── 본 게임 화면 ─────────────────────────────────────────
    else:
        game = st.session_state.game

        if st.sidebar.button("게임 강제 종료 (로비로 돌아가기)"):
            st.session_state.clear()
            st.rerun()

        # 게임 종료
        if st.session_state.get('game_over', False) or game.current_turn > game.total_turns:
            st.header("🏁 게임이 종료되었습니다!")
            st.markdown("### 최종 결과")
            results = [
                (t.name, t.get_total_value_krw(game.get_price, game.current_date))
                for t in game.teams
            ]
            for name, val in results:
                st.write(f"**{name}** 총 자산: {val:,.0f} 원")
            winner = max(results, key=lambda x: x[1])
            st.success(f"🥇 최종 우승팀은 **{winner[0]}** 입니다!")
            with st.expander("게임에서 배운 점 확인하기 (경제 지식 브리핑)", expanded=True):
                st.markdown("""
                * **환율 변동성(FX Risk):** 미국 주식 투자 시 환율 변동에 따른 환차손과 수수료의 중요성을 체감했습니다.
                * **거시 경제와 주식 시장:** 퀴즈를 통해 본 경제 상황이 주가에 미치는 영향을 확인했습니다.
                * **기회비용과 자산 배분:** 제한된 자본으로 현금 보유 vs 주식 투자 결정은 모두 기회비용이었습니다.
                * **장기 투자와 복리:** 시장의 오르내림 속에서도 우량 자산을 믿고 버티는 투자의 힘을 경험했습니다.
                """)
            return

        # 턴 헤더
        st.header(f"현재 턴: {game.current_turn} / {game.total_turns}")
        st.subheader(f"📅 현재 날짜: {game.current_date.strftime('%Y년 %m월 %d일')}")
        st.markdown("---")

        # ── 경제 퀴즈 + 실시간 뉴스 섹션 ──
        st.subheader("📰 이번 달 경제 퀴즈 & 뉴스")
        quiz = st.session_state.current_quiz

        if quiz:
            if not st.session_state.quiz_answered:
                st.info("✅ 퀴즈를 맞히면 이번 달 실제 핵심 뉴스가 공개됩니다! (기회는 한 번)")
                st.write(f"**Q. {quiz['question']}**")
                user_choice = st.radio(
                    "정답 선택:",
                    quiz['options'],
                    index=0,
                    key=f"quiz_radio_{game.current_turn}"
                )
                if st.button("정답 제출"):
                    selected_num = int(user_choice.split(".")[0])
                    st.session_state.quiz_answered = True
                    st.session_state.news_unlocked = (selected_num == quiz['answer'])
                    st.rerun()

            else:  # 퀴즈 답변 후
                if st.session_state.news_unlocked:
                    # 정답 → 실제 역사 뉴스 fetch
                    year_month_label = game.current_date.strftime('%Y년 %#m월') \
                        if hasattr(game.current_date, 'strftime') else game.current_date.strftime('%Y년 %-m월')
                    # Windows 호환: %#m, Linux: %-m
                    try:
                        year_month_label = game.current_date.strftime('%Y년 %#m월')
                    except ValueError:
                        year_month_label = game.current_date.strftime('%Y년 %-m월')

                    st.success("🎉 정답입니다! 이번 달 주요 경제 뉴스를 불러옵니다...")

                    if api_key:
                        with st.spinner("뉴스 로딩 중..."):
                            news_text = fetch_historical_news(year_month_label, api_key)
                        st.markdown(f"### 📌 {year_month_label} 주요 경제 뉴스")
                        st.markdown(news_text)
                    else:
                        st.warning("📢 Anthropic API 키를 사이드바에 입력하면 실제 뉴스가 표시됩니다.")
                else:
                    st.error("❌ 오답입니다. 이번 달 시장 정보는 공개되지 않습니다.")
        else:
            st.write("준비된 퀴즈가 모두 소진되었습니다.")

        st.markdown("---")

        # ── 팀별 대시보드 ──
        tabs = st.tabs([team.name for team in game.teams])
        for i, team in enumerate(game.teams):
            with tabs[i]:
                if team.is_bankrupt:
                    st.error("💀 파산한 팀입니다. 자산 가치가 초기 자본의 10% 미만으로 떨어졌습니다.")
                    continue

                total_val = team.get_total_value_krw(game.get_price, game.current_date)
                st.metric("총 자산 평가액 (원)", f"{total_val:,.0f}")
                col1, col2 = st.columns(2)
                col1.metric("보유 원화 (KRW)", f"{team.krw_balance:,.0f}")
                col2.metric("보유 달러 (USD)", f"${team.usd_balance:,.2f}")

                st.markdown("##### 📊 현재 포트폴리오")
                display_portfolio_ui(team, game.get_price, game.current_date)
                st.markdown("---")

                trade_col, exch_col = st.columns(2)

                # ── 주식 거래 (슬라이더) ──
                with trade_col:
                    st.write("**📈 주식 거래**")
                    trade_ticker = st.selectbox(
                        "종목 선택",
                        game.tradeable_tickers,
                        format_func=ticker_label,       # ← 한글명 표시
                        key=f"ticker_{team.name}"
                    )

                    trade_shares = make_shares_slider(
                        "거래 수량",
                        team, trade_ticker, game,
                        key=f"shares_{team.name}_{game.current_turn}"
                    )

                    # 예상 금액 미리 표시
                    price_now = game.get_price(trade_ticker, game.current_date)
                    is_kr_trade = trade_ticker.endswith('.KS')
                    if price_now > 0:
                        est = price_now * trade_shares
                        if is_kr_trade:
                            st.caption(f"예상 금액: **{est:,.0f} 원**")
                        else:
                            st.caption(f"예상 금액: **${est:,.2f}**")

                    t_btn1, t_btn2 = st.columns(2)
                    if t_btn1.button("매수 (Buy)", key=f"buy_{team.name}"):
                        ok, msg = game.buy_stock(team, trade_ticker, trade_shares)
                        st.success(msg) if ok else st.error(msg)
                    if t_btn2.button("매도 (Sell)", key=f"sell_{team.name}"):
                        ok, msg = game.sell_stock(team, trade_ticker, trade_shares)
                        st.success(msg) if ok else st.error(msg)

                # ── 환전 (환율 표시 추가) ──
                with exch_col:
                    st.write("**💱 환전**")
                    # 현재 환율 표시
                    cur_rate = game.get_price('USDKRW=X', game.current_date)
                    show_exchange_rate_box(cur_rate)

                    exch_amount = st.number_input(
                        "환전 기준 금액 (달러)",
                        min_value=100.0, step=100.0,
                        key=f"exch_{team.name}"
                    )
                    e_btn1, e_btn2 = st.columns(2)
                    if e_btn1.button("달러 매수 →", key=f"buy_usd_{team.name}"):
                        ok, msg = game.exchange_currency(team, 'KRW_TO_USD', exch_amount)
                        st.success(msg) if ok else st.error(msg)
                    if e_btn2.button("← 달러 매도", key=f"sell_usd_{team.name}"):
                        ok, msg = game.exchange_currency(team, 'USD_TO_KRW', exch_amount)
                        st.success(msg) if ok else st.error(msg)

        # ── 다음 턴 ──
        st.markdown("---")
        if st.button("⏭️ 다음 턴으로 이동 (1개월 후)"):
            game.next_turn()
            st.session_state.quiz_answered = False
            st.session_state.news_unlocked = False
            st.session_state.current_quiz = (
                game.quizzes.pop() if game.quizzes else None
            )
            if game.current_turn > game.total_turns:
                st.session_state.game_over = True
            st.rerun()


if __name__ == "__main__":
    main()
