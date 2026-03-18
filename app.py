import streamlit as st
import pandas as pd
import yfinance as yf
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ==========================================
# 1. 팀 및 자산 관리 클래스
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
# 2. 게임 시스템 및 로직 클래스
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
        if start_date_choice in self.start_dates_pool:
            chosen_date = start_date_choice
        else:
            chosen_date = random.choice(self.start_dates_pool)

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
        # [BUG FIX 1] 거래 가능 종목에서 USDKRW=X 분리
        # all_tickers는 데이터 다운로드용, tradeable_tickers는 매수/매도 선택용
        self.tradeable_tickers = self.us_tickers + self.kr_tickers
        self.all_tickers = self.tradeable_tickers + ['USDKRW=X']

        self.market_data = pd.DataFrame()

        self.quizzes = [
            {"question": "선택으로 인해 포기해야 하는 대안 중 가장 가치 있는 것은?", "options": ["1. 매몰비용", "2. 기회비용", "3. 한계비용"], "answer": 2, "news_snippet": "투자자들, 안전자산 대신 주식 시장으로 이동하며 기회비용 고려!"},
            {"question": "사람들의 욕망은 무한하지만, 자원은 한정되어 있는 상태는?", "options": ["1. 희소성", "2. 효율성", "3. 형평성"], "answer": 1, "news_snippet": "희소성 높은 희토류 관련 기업 주가 폭등!"},
            {"question": "다른 조건이 같을 때, 가격이 오르면 그 상품의 수요량은 어떻게 될까요?", "options": ["1. 증가한다", "2. 감소한다", "3. 변동 없다"], "answer": 2, "news_snippet": "제품 가격 인상 여파로 소비자 수요 급감 우려."},
            {"question": "콜라와 사이다처럼 한 재화의 가격이 오를 때 다른 재화의 수요가 증가하는 관계는?", "options": ["1. 보완재", "2. 정상재", "3. 대체재"], "answer": 3, "news_snippet": "원자재 가격 폭등으로 대체재 관련주 동반 상승!"},
            {"question": "스마트폰과 충전기처럼 함께 소비할 때 만족감이 커지는 재화는?", "options": ["1. 보완재", "2. 대체재", "3. 열등재"], "answer": 1, "news_snippet": "전기차 판매량 증가에 배터리(보완재) 기업 주가도 방긋."},
            {"question": "시장에서 수요량과 공급량이 일치하여 결정되는 가격은?", "options": ["1. 최고가격", "2. 균형가격", "3. 최저가격"], "answer": 2, "news_snippet": "원유 시장, 수요와 공급 안정화되며 균형가격 찾기 돌입."},
            {"question": "물가가 지속적으로 오르고 화폐 가치가 떨어지는 현상은?", "options": ["1. 디플레이션", "2. 스태그플레이션", "3. 인플레이션"], "answer": 3, "news_snippet": "글로벌 인플레이션 우려로 중앙은행 긴급 회의 소집."},
            {"question": "인플레이션이 발생했을 때 일반적으로 더 유리해지는 사람은?", "options": ["1. 현금 보유자", "2. 돈을 빌린 사람", "3. 돈을 빌려준 사람"], "answer": 2, "news_snippet": "물가 상승으로 실질 부채 부담 감소, 기업들 투자 확대 조짐."},
            {"question": "물가가 지속적으로 하락하며 경제 활동이 침체되는 현상은?", "options": ["1. 인플레이션", "2. 디플레이션", "3. 리디노미네이션"], "answer": 2, "news_snippet": "소비 위축과 디플레이션 공포에 주식 시장 얼어붙어..."},
            {"question": "중앙은행이 물가를 안정시키기 위해 시중 통화량을 줄이려 할 때 취할 행동은?", "options": ["1. 기준금리 인상", "2. 기준금리 인하", "3. 세금 감면"], "answer": 1, "news_snippet": "중앙은행 기습 금리 인상 발표! 증시 자금 이탈 가속화."},
            {"question": "외국 화폐에 대한 자국 화폐의 교환 비율은?", "options": ["1. 금리", "2. 물가", "3. 환율"], "answer": 3, "news_snippet": "외환시장 변동성 확대, 환율 방어를 위한 당국 개입 시사."},
            {"question": "원/달러 환율이 올랐습니다. 이때 웃게 되는 사람은?", "options": ["1. 해외 여행객", "2. 수입업자", "3. 수출업자"], "answer": 3, "news_snippet": "환율 급등으로 수출 주도 기업 실적 호조 예상!"},
            {"question": "원/달러 환율이 떨어졌습니다. 이때 피해를 볼 가능성이 큰 사람은?", "options": ["1. 유학생 부모", "2. 부품 수입 기업", "3. 수출 기업"], "answer": 3, "news_snippet": "원화 강세(환율 하락)로 수출 기업 가격 경쟁력 비상!"},
            {"question": "일정 기간 한 나라 안에서 새로 생산된 최종 생산물의 가치 합은?", "options": ["1. 물가지수", "2. 국내총생산(GDP)", "3. 국민총소득(GNI)"], "answer": 2, "news_snippet": "올해 GDP 성장률 예상치 상회! 증시에 강력한 훈풍."},
            {"question": "소득이 많은 사람에게 더 높은 비율의 세금을 거두는 제도는?", "options": ["1. 비례세", "2. 누진세", "3. 역진세"], "answer": 2, "news_snippet": "고소득층 누진세율 인상 법안 통과, 부유층 자산 이동 시작."},
            {"question": "납세자와 담세자가 다른 세금은?", "options": ["1. 간접세", "2. 직접세", "3. 소득세"], "answer": 1, "news_snippet": "부가가치세(간접세) 개편 논의에 소비재 관련 주가 출렁."},
            {"question": "한 기업이 시장을 장악하여 가격을 마음대로 결정할 수 있는 시장은?", "options": ["1. 완전경쟁시장", "2. 독점시장", "3. 과점시장"], "answer": 2, "news_snippet": "특정 빅테크 기업의 독점 논란, 정부 규제 칼 빼들어 주가 급락!"},
            {"question": "소수의 기업이 시장을 지배하며 눈치를 보며 경쟁하는 시장은?", "options": ["1. 독점시장", "2. 과점시장", "3. 완전경쟁시장"], "answer": 2, "news_snippet": "통신사들의 치열한 마케팅 전쟁, 수익성 악화 우려."},
            {"question": "어떤 활동이 타인에게 의도치 않은 혜택을 주는데도 대가를 받지 못하는 상황은?", "options": ["1. 긍정적 외부효과", "2. 부정적 외부효과", "3. 무임승차"], "answer": 1, "news_snippet": "친환경 기업, 긍정적 외부효과 인정받아 정부 보조금 획득!"},
            {"question": "국방 서비스처럼 돈을 내지 않은 사람도 이용할 수 있는 재화는?", "options": ["1. 사유재", "2. 공공재", "3. 대체재"], "answer": 2, "news_snippet": "정부, 대규모 공공재 인프라 투자 발표... 건설주 상한가!"},
            {"question": "더 적은 기회비용으로 생산할 수 있는 상품에 집중하는 원리는?", "options": ["1. 절대우위", "2. 보호무역", "3. 비교우위"], "answer": 3, "news_snippet": "양국 비교우위 살린 무역 협정 체결, 무역량 폭발적 증가 기대."},
            {"question": "자국 산업을 보호하기 위해 수입품에 높은 관세를 매기는 정책은?", "options": ["1. 자유무역", "2. 보호무역", "3. 공정무역"], "answer": 2, "news_snippet": "강대국 보호무역주의 강화, 관세 폭탄 우려에 신흥국 증시 발작."},
            {"question": "원금뿐만 아니라 원금에서 생겨난 이자에도 이자가 붙는 계산 방식은?", "options": ["1. 단리", "2. 복리", "3. 마이너스 금리"], "answer": 2, "news_snippet": "복리의 마법! 장기 투자 펀드 수익률, 역대 최고치 경신."},
            {"question": "회사가 이익을 내서 그 이익의 일부를 주주들에게 나누어 주는 돈은?", "options": ["1. 이자", "2. 배당금", "3. 세금"], "answer": 2, "news_snippet": "연말 배당 시즌 도래, 고배당주에 투자자들 수백억 몰려."},
            {"question": "호황기를 지나 침체기로 접어드는 등 경제 상태가 변하는 것은?", "options": ["1. 경제성장", "2. 경기변동", "3. 인플레이션"], "answer": 2, "news_snippet": "경기변동 사이클 상 하락 국면 진입? 전문가들 방어주 투자 권고."},
            {"question": "직장을 구하려는 의지가 있음에도 일자리를 구하지 못한 상태는?", "options": ["1. 고용", "2. 실업", "3. 은퇴"], "answer": 2, "news_snippet": "실업률 통계치 발표 쇼크, 소비 둔화 우려로 유통주 하락."},
            {"question": "개인이나 기업이 발명, 상표 등에 대해 가지는 독점적인 권리는?", "options": ["1. 소유권", "2. 지적재산권", "3. 영업권"], "answer": 2, "news_snippet": "바이오 기업, 핵심 지적재산권 승소로 주가 폭등!"},
            {"question": "시장에서 가격이 수요와 공급을 조절하는 기능을 빗댄 애덤 스미스의 말은?", "options": ["1. 보이지 않는 손", "2. 보이는 손", "3. 황금 손"], "answer": 1, "news_snippet": "정부 개입 논란, '보이지 않는 손'에 맡겨야 한다는 목소리."},
            {"question": "가계가 노동이나 자본을 제공하고 얻는 대가는?", "options": ["1. 지출", "2. 소득", "3. 부채"], "answer": 2, "news_snippet": "국민 가계 소득 증가율 둔화, 내수 시장 침체로 이어질까 촉각."},
            {"question": "일반적으로 예금 금리와 대출 금리 중 어느 것이 더 높을까요?", "options": ["1. 예금 금리", "2. 대출 금리", "3. 항상 같다"], "answer": 2, "news_snippet": "예금과 대출 금리 차이 확대로 금융주 사상 최대 실적!"},
            {"question": "정부가 경제를 살리기 위해 세금을 줄이고 지출을 늘리는 정책은?", "options": ["1. 긴축 재정", "2. 확대 재정", "3. 통화 정책"], "answer": 2, "news_snippet": "정부 대규모 확대 재정 편성, 시장에 유동성 공급 기대감."},
            {"question": "앞으로 주가가 오를 것으로 기대하는 상승장을 상징하는 동물은?", "options": ["1. 곰(Bear)", "2. 황소(Bull)", "3. 독수리(Eagle)"], "answer": 2, "news_snippet": "월가에 황소(Bull)가 돌아왔다! 증시 연일 최고점 돌파."},
            {"question": "앞으로 주가가 떨어질 것으로 예상하는 하락장을 상징하는 동물은?", "options": ["1. 곰(Bear)", "2. 황소(Bull)", "3. 사자(Lion)"], "answer": 1, "news_snippet": "베어마켓(Bear Market) 공포 확산, 투자자들 현금 확보 비상."},
            {"question": "기업이 새로 주식을 발행하여 사람들에게 처음으로 파는 과정을 뜻하는 약자는?", "options": ["1. GDP", "2. IPO", "3. M&A"], "answer": 2, "news_snippet": "하반기 최대어 기업 IPO 돌입, 공모주 청약에 수십조 쏠려."},
            {"question": "두 개 이상의 기업이 하나로 합쳐지거나 다른 기업을 사들이는 것을 뜻하는 약자는?", "options": ["1. M&A", "2. IPO", "3. CEO"], "answer": 1, "news_snippet": "빅테크 기업들의 초대형 M&A 발표! 관련주 상한가 직행."}
        ]
        random.shuffle(self.quizzes)

    def load_market_data(self):
        end_date = self.current_date + relativedelta(months=self.total_turns + 2)

        # [BUG FIX 2] yfinance 최신 버전의 MultiIndex 컬럼 구조 안정적으로 처리
        raw = yf.download(
            self.all_tickers,
            start=self.current_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            progress=False,
            auto_adjust=True   # 수정 주가(adjusted close) 사용
        )

        # yfinance 버전에 따라 컬럼 구조가 다를 수 있으므로 안전하게 처리
        if isinstance(raw.columns, pd.MultiIndex):
            # 최신 yfinance: ('Close', 'AAPL') 형태의 MultiIndex
            if 'Close' in raw.columns.get_level_values(0):
                self.market_data = raw['Close']
            elif 'Price' in raw.columns.get_level_values(0):
                self.market_data = raw['Price']
            else:
                # 첫 번째 레벨의 첫 항목 사용 (fallback)
                self.market_data = raw[raw.columns.get_level_values(0)[0]]
        else:
            # 단일 종목이거나 구버전 yfinance
            self.market_data = raw

        # DatetimeIndex가 timezone-aware인 경우 timezone 제거 (비교 오류 방지)
        if hasattr(self.market_data.index, 'tz') and self.market_data.index.tz is not None:
            self.market_data.index = self.market_data.index.tz_localize(None)

    def get_price(self, ticker, date):
        if self.market_data.empty:
            return 0.0

        date_str = date.strftime('%Y-%m-%d')

        try:
            # [BUG FIX 3] loc 슬라이싱 실패 대비 try/except 추가
            subset = self.market_data.loc[date_str:]
            if not subset.empty and ticker in subset.columns:
                valid_prices = subset[ticker].dropna()
                if not valid_prices.empty:
                    return float(valid_prices.iloc[0])
        except (KeyError, TypeError):
            pass

        return 0.0

    def buy_stock(self, team, ticker, shares):
        price = self.get_price(ticker, self.current_date)
        if price == 0:
            return False, "현재 거래할 수 없는 주식입니다."

        is_kr = ticker.endswith('.KS')
        required_money = price * shares

        if (is_kr and team.krw_balance >= required_money) or \
           (not is_kr and team.usd_balance >= required_money):
            if is_kr:
                team.krw_balance -= required_money
            else:
                team.usd_balance -= required_money

            if ticker in team.portfolio:
                old_shares = team.portfolio[ticker]['shares']
                old_avg = team.portfolio[ticker]['avg_price']
                new_shares = old_shares + shares
                new_avg = ((old_shares * old_avg) + (shares * price)) / new_shares
                team.portfolio[ticker] = {'shares': new_shares, 'avg_price': new_avg}
            else:
                team.portfolio[ticker] = {'shares': shares, 'avg_price': price}

            return True, f"[{team.name}] {ticker} {shares}주 매수 완료!"
        else:
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

        return True, f"[{team.name}] {ticker} {shares}주 매도 완료!"

    def exchange_currency(self, team, direction, amount_usd):
        exchange_rate = self.get_price('USDKRW=X', self.current_date)
        if exchange_rate == 0:
            exchange_rate = 1300.0

        if direction == 'KRW_TO_USD':
            applied_rate = exchange_rate * 1.05
            required_krw = amount_usd * applied_rate
            if team.krw_balance >= required_krw:
                team.krw_balance -= required_krw
                team.usd_balance += amount_usd
                return True, f"{amount_usd:,.0f}달러 구매 완료 (적용 환율: {applied_rate:,.2f}원)"
            return False, "원화 잔고가 부족합니다."

        elif direction == 'USD_TO_KRW':
            applied_rate = exchange_rate * 0.95
            received_krw = amount_usd * applied_rate
            if team.usd_balance >= amount_usd:
                team.usd_balance -= amount_usd
                team.krw_balance += received_krw
                return True, f"{received_krw:,.0f}원 획득 완료 (적용 환율: {applied_rate:,.2f}원)"
            return False, "달러 잔고가 부족합니다."

    def check_bankruptcy(self, team):
        initial_value = 230000000
        current_value = team.get_total_value_krw(self.get_price, self.current_date)
        if current_value < (initial_value * 0.1):
            team.is_bankrupt = True

    def next_turn(self):
        for team in self.teams:
            if not team.is_bankrupt:
                self.check_bankruptcy(team)
        self.current_turn += 1
        self.current_date += relativedelta(months=1)


# ==========================================
# 3. UI 렌더링 헬퍼 함수
# ==========================================
def display_portfolio_ui(team, get_price_func, current_date):
    if not team.portfolio:
        st.info("현재 보유 중인 주식이 없습니다.")
        return

    portfolio_data = []
    for ticker, info in team.portfolio.items():
        shares = info['shares']
        avg_price = info['avg_price']
        current_price = get_price_func(ticker, current_date)

        return_rate = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0
        currency = "KRW" if ticker.endswith('.KS') else "USD"

        avg_str = f"${avg_price:,.2f}" if currency == "USD" else f"{avg_price:,.0f}원"
        cur_str = f"${current_price:,.2f}" if currency == "USD" else f"{current_price:,.0f}원"

        portfolio_data.append({
            "종목명": ticker,
            "수량": shares,
            "평단가": avg_str,
            "현재가": cur_str,
            "수익률": f"{return_rate:+.2f}%"
        })

    df = pd.DataFrame(portfolio_data)

    # [BUG FIX 4] pandas 버전에 따라 style.applymap → style.map 변경됨
    # pandas < 2.1: applymap / pandas >= 2.1: map (applymap deprecated)
    def color_return(val):
        if '+' in val:
            return 'color: red'
        elif '-' in val:
            return 'color: blue'
        return 'color: black'

    try:
        styled_df = df.style.map(color_return, subset=['수익률'])
    except AttributeError:
        styled_df = df.style.applymap(color_return, subset=['수익률'])

    st.dataframe(styled_df, use_container_width=True, hide_index=True)


# ==========================================
# 4. Streamlit 메인 앱 로직
# ==========================================
def main():
    st.set_page_config(page_title="글로벌 모의투자 게임", layout="wide")
    st.title("글로벌 모의투자 보드게임")

    if 'game_started' not in st.session_state:
        st.session_state.game_started = False

    # --- [화면 1] 로비 화면 ---
    if not st.session_state.game_started:
        st.subheader("게임 세팅 로비")
        with st.form("lobby_form"):
            st.markdown("#### 1. 게임 기본 설정")
            col1, col2 = st.columns(2)
            total_turns = col1.slider("총 게임 길이 (턴/개월)", min_value=8, max_value=18, value=12)
            start_dates = ['random', '2001-01-01', '2005-05-01', '2010-01-01', '2015-05-01', '2020-01-01', '2023-01-01']
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

                    if st.session_state.game.quizzes:
                        st.session_state.current_quiz = st.session_state.game.quizzes.pop()
                    else:
                        st.session_state.current_quiz = None

                    st.session_state.game_started = True
                st.rerun()

    # --- [화면 2] 본 게임 화면 ---
    else:
        game = st.session_state.game

        if st.sidebar.button("게임 강제 종료 (로비로 돌아가기)"):
            st.session_state.clear()
            st.rerun()

        # 게임 종료 처리 및 브리핑
        if st.session_state.get('game_over', False) or game.current_turn > game.total_turns:
            st.header("게임이 종료되었습니다!")
            st.markdown("### 최종 결과")
            results = []
            for team in game.teams:
                final_val = team.get_total_value_krw(game.get_price, game.current_date)
                results.append((team.name, final_val))
                st.write(f"**{team.name}** 총 자산: {final_val:,.0f} 원")

            winner = max(results, key=lambda x: x[1])
            st.success(f"최종 우승팀은 **{winner[0]}** 입니다!")

            with st.expander("게임에서 배운 점 확인하기 (경제 지식 브리핑)", expanded=True):
                st.markdown("""
                * **환율 변동성(FX Risk):** 미국 주식 투자 시 환율 변동에 따른 환차손과 수수료의 중요성을 체감했습니다.
                * **거시 경제와 주식 시장:** 퀴즈를 통해 본 경제 상황이 주가에 미치는 영향을 확인했습니다.
                * **기회비용과 자산 배분:** 제한된 자본으로 현금을 보유할지, 주식에 투자할지 결정하는 모든 순간이 기회비용이었습니다.
                * **장기 투자와 복리:** 시장의 오르내림 속에서도 우량 자산을 믿고 버티는 투자의 힘을 경험했습니다.
                """)
            return

        # 턴 현황
        st.header(f"현재 턴: {game.current_turn} / {game.total_turns}")
        st.subheader(f"현재 날짜: {game.current_date.strftime('%Y-%m-%d')}")
        st.markdown("---")

        # 경제 퀴즈
        st.subheader("이번 달 경제 뉴스 퀴즈")
        if st.session_state.current_quiz:
            quiz = st.session_state.current_quiz
            if not st.session_state.quiz_answered:
                st.info("퀴즈를 맞히면 시장의 흐름을 읽을 수 있는 핵심 뉴스가 공개됩니다. (기회는 한 번!)")
                st.write(f"**Q. {quiz['question']}**")

                # [BUG FIX 5] st.radio의 index 기본값 명시 → 매 턴마다 초기화 보장
                user_choice = st.radio("정답 선택:", quiz['options'], index=0, key=f"quiz_radio_{game.current_turn}")

                if st.button("정답 제출"):
                    st.session_state.quiz_answered = True
                    selected_num = int(user_choice.split(".")[0])
                    st.session_state.news_unlocked = (selected_num == quiz['answer'])
                    st.rerun()
            else:
                if st.session_state.news_unlocked:
                    st.success(f"**[핵심 뉴스 획득]**\n\n{quiz['news_snippet']}")
                else:
                    st.error("오답입니다. 이번 달 시장 정보는 제공되지 않습니다.")
        else:
            st.write("준비된 퀴즈가 모두 소진되었습니다.")
        st.markdown("---")

        # 팀별 자산 및 거래 대시보드
        tabs = st.tabs([team.name for team in game.teams])
        for i, team in enumerate(game.teams):
            with tabs[i]:
                if team.is_bankrupt:
                    st.error("파산한 팀입니다. 자산 가치가 초기 자본의 10% 미만으로 떨어졌습니다.")
                    continue

                total_val = team.get_total_value_krw(game.get_price, game.current_date)
                st.metric("총 자산 평가액 (원)", f"{total_val:,.0f}")

                col1, col2 = st.columns(2)
                col1.metric("보유 원화 (KRW)", f"{team.krw_balance:,.0f}")
                col2.metric("보유 달러 (USD)", f"{team.usd_balance:,.2f}")

                st.markdown("##### 현재 포트폴리오")
                display_portfolio_ui(team, game.get_price, game.current_date)

                st.markdown("---")

                trade_col, exch_col = st.columns(2)

                with trade_col:
                    st.write("**주식 거래**")
                    # [BUG FIX 1 적용] USDKRW=X 제외한 tradeable_tickers만 표시
                    trade_ticker = st.selectbox(
                        "종목 선택",
                        game.tradeable_tickers,
                        key=f"ticker_{team.name}"
                    )
                    trade_shares = st.number_input(
                        "거래 수량", min_value=1, step=1,
                        key=f"shares_{team.name}"
                    )

                    t_btn1, t_btn2 = st.columns(2)
                    if t_btn1.button("매수 (Buy)", key=f"buy_{team.name}"):
                        success, msg = game.buy_stock(team, trade_ticker, trade_shares)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    if t_btn2.button("매도 (Sell)", key=f"sell_{team.name}"):
                        success, msg = game.sell_stock(team, trade_ticker, trade_shares)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)

                with exch_col:
                    st.write("**환전 (수수료 5% 적용)**")
                    exch_amount = st.number_input(
                        "환전 기준 금액 (달러)", min_value=100.0, step=100.0,
                        key=f"exch_{team.name}"
                    )

                    e_btn1, e_btn2 = st.columns(2)
                    if e_btn1.button("달러 구매", key=f"buy_usd_{team.name}"):
                        success, msg = game.exchange_currency(team, 'KRW_TO_USD', exch_amount)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    if e_btn2.button("달러 판매", key=f"sell_usd_{team.name}"):
                        success, msg = game.exchange_currency(team, 'USD_TO_KRW', exch_amount)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)

        # 턴 종료 버튼
        st.markdown("---")
        if st.button("다음 턴으로 이동 (1개월 후)"):
            game.next_turn()
            st.session_state.quiz_answered = False
            st.session_state.news_unlocked = False

            if st.session_state.game.quizzes:
                st.session_state.current_quiz = st.session_state.game.quizzes.pop()
            else:
                st.session_state.current_quiz = None

            if game.current_turn > game.total_turns:
                st.session_state.game_over = True

            st.rerun()


if __name__ == "__main__":
    main()import streamlit as st
import pandas as pd
import yfinance as yf
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ==========================================
# 1. 팀 및 자산 관리 클래스
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
# 2. 게임 시스템 및 로직 클래스
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
        if start_date_choice in self.start_dates_pool:
            chosen_date = start_date_choice
        else:
            chosen_date = random.choice(self.start_dates_pool)

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
        # [BUG FIX 1] 거래 가능 종목에서 USDKRW=X 분리
        # all_tickers는 데이터 다운로드용, tradeable_tickers는 매수/매도 선택용
        self.tradeable_tickers = self.us_tickers + self.kr_tickers
        self.all_tickers = self.tradeable_tickers + ['USDKRW=X']

        self.market_data = pd.DataFrame()

        self.quizzes = [
            {"question": "선택으로 인해 포기해야 하는 대안 중 가장 가치 있는 것은?", "options": ["1. 매몰비용", "2. 기회비용", "3. 한계비용"], "answer": 2, "news_snippet": "투자자들, 안전자산 대신 주식 시장으로 이동하며 기회비용 고려!"},
            {"question": "사람들의 욕망은 무한하지만, 자원은 한정되어 있는 상태는?", "options": ["1. 희소성", "2. 효율성", "3. 형평성"], "answer": 1, "news_snippet": "희소성 높은 희토류 관련 기업 주가 폭등!"},
            {"question": "다른 조건이 같을 때, 가격이 오르면 그 상품의 수요량은 어떻게 될까요?", "options": ["1. 증가한다", "2. 감소한다", "3. 변동 없다"], "answer": 2, "news_snippet": "제품 가격 인상 여파로 소비자 수요 급감 우려."},
            {"question": "콜라와 사이다처럼 한 재화의 가격이 오를 때 다른 재화의 수요가 증가하는 관계는?", "options": ["1. 보완재", "2. 정상재", "3. 대체재"], "answer": 3, "news_snippet": "원자재 가격 폭등으로 대체재 관련주 동반 상승!"},
            {"question": "스마트폰과 충전기처럼 함께 소비할 때 만족감이 커지는 재화는?", "options": ["1. 보완재", "2. 대체재", "3. 열등재"], "answer": 1, "news_snippet": "전기차 판매량 증가에 배터리(보완재) 기업 주가도 방긋."},
            {"question": "시장에서 수요량과 공급량이 일치하여 결정되는 가격은?", "options": ["1. 최고가격", "2. 균형가격", "3. 최저가격"], "answer": 2, "news_snippet": "원유 시장, 수요와 공급 안정화되며 균형가격 찾기 돌입."},
            {"question": "물가가 지속적으로 오르고 화폐 가치가 떨어지는 현상은?", "options": ["1. 디플레이션", "2. 스태그플레이션", "3. 인플레이션"], "answer": 3, "news_snippet": "글로벌 인플레이션 우려로 중앙은행 긴급 회의 소집."},
            {"question": "인플레이션이 발생했을 때 일반적으로 더 유리해지는 사람은?", "options": ["1. 현금 보유자", "2. 돈을 빌린 사람", "3. 돈을 빌려준 사람"], "answer": 2, "news_snippet": "물가 상승으로 실질 부채 부담 감소, 기업들 투자 확대 조짐."},
            {"question": "물가가 지속적으로 하락하며 경제 활동이 침체되는 현상은?", "options": ["1. 인플레이션", "2. 디플레이션", "3. 리디노미네이션"], "answer": 2, "news_snippet": "소비 위축과 디플레이션 공포에 주식 시장 얼어붙어..."},
            {"question": "중앙은행이 물가를 안정시키기 위해 시중 통화량을 줄이려 할 때 취할 행동은?", "options": ["1. 기준금리 인상", "2. 기준금리 인하", "3. 세금 감면"], "answer": 1, "news_snippet": "중앙은행 기습 금리 인상 발표! 증시 자금 이탈 가속화."},
            {"question": "외국 화폐에 대한 자국 화폐의 교환 비율은?", "options": ["1. 금리", "2. 물가", "3. 환율"], "answer": 3, "news_snippet": "외환시장 변동성 확대, 환율 방어를 위한 당국 개입 시사."},
            {"question": "원/달러 환율이 올랐습니다. 이때 웃게 되는 사람은?", "options": ["1. 해외 여행객", "2. 수입업자", "3. 수출업자"], "answer": 3, "news_snippet": "환율 급등으로 수출 주도 기업 실적 호조 예상!"},
            {"question": "원/달러 환율이 떨어졌습니다. 이때 피해를 볼 가능성이 큰 사람은?", "options": ["1. 유학생 부모", "2. 부품 수입 기업", "3. 수출 기업"], "answer": 3, "news_snippet": "원화 강세(환율 하락)로 수출 기업 가격 경쟁력 비상!"},
            {"question": "일정 기간 한 나라 안에서 새로 생산된 최종 생산물의 가치 합은?", "options": ["1. 물가지수", "2. 국내총생산(GDP)", "3. 국민총소득(GNI)"], "answer": 2, "news_snippet": "올해 GDP 성장률 예상치 상회! 증시에 강력한 훈풍."},
            {"question": "소득이 많은 사람에게 더 높은 비율의 세금을 거두는 제도는?", "options": ["1. 비례세", "2. 누진세", "3. 역진세"], "answer": 2, "news_snippet": "고소득층 누진세율 인상 법안 통과, 부유층 자산 이동 시작."},
            {"question": "납세자와 담세자가 다른 세금은?", "options": ["1. 간접세", "2. 직접세", "3. 소득세"], "answer": 1, "news_snippet": "부가가치세(간접세) 개편 논의에 소비재 관련 주가 출렁."},
            {"question": "한 기업이 시장을 장악하여 가격을 마음대로 결정할 수 있는 시장은?", "options": ["1. 완전경쟁시장", "2. 독점시장", "3. 과점시장"], "answer": 2, "news_snippet": "특정 빅테크 기업의 독점 논란, 정부 규제 칼 빼들어 주가 급락!"},
            {"question": "소수의 기업이 시장을 지배하며 눈치를 보며 경쟁하는 시장은?", "options": ["1. 독점시장", "2. 과점시장", "3. 완전경쟁시장"], "answer": 2, "news_snippet": "통신사들의 치열한 마케팅 전쟁, 수익성 악화 우려."},
            {"question": "어떤 활동이 타인에게 의도치 않은 혜택을 주는데도 대가를 받지 못하는 상황은?", "options": ["1. 긍정적 외부효과", "2. 부정적 외부효과", "3. 무임승차"], "answer": 1, "news_snippet": "친환경 기업, 긍정적 외부효과 인정받아 정부 보조금 획득!"},
            {"question": "국방 서비스처럼 돈을 내지 않은 사람도 이용할 수 있는 재화는?", "options": ["1. 사유재", "2. 공공재", "3. 대체재"], "answer": 2, "news_snippet": "정부, 대규모 공공재 인프라 투자 발표... 건설주 상한가!"},
            {"question": "더 적은 기회비용으로 생산할 수 있는 상품에 집중하는 원리는?", "options": ["1. 절대우위", "2. 보호무역", "3. 비교우위"], "answer": 3, "news_snippet": "양국 비교우위 살린 무역 협정 체결, 무역량 폭발적 증가 기대."},
            {"question": "자국 산업을 보호하기 위해 수입품에 높은 관세를 매기는 정책은?", "options": ["1. 자유무역", "2. 보호무역", "3. 공정무역"], "answer": 2, "news_snippet": "강대국 보호무역주의 강화, 관세 폭탄 우려에 신흥국 증시 발작."},
            {"question": "원금뿐만 아니라 원금에서 생겨난 이자에도 이자가 붙는 계산 방식은?", "options": ["1. 단리", "2. 복리", "3. 마이너스 금리"], "answer": 2, "news_snippet": "복리의 마법! 장기 투자 펀드 수익률, 역대 최고치 경신."},
            {"question": "회사가 이익을 내서 그 이익의 일부를 주주들에게 나누어 주는 돈은?", "options": ["1. 이자", "2. 배당금", "3. 세금"], "answer": 2, "news_snippet": "연말 배당 시즌 도래, 고배당주에 투자자들 수백억 몰려."},
            {"question": "호황기를 지나 침체기로 접어드는 등 경제 상태가 변하는 것은?", "options": ["1. 경제성장", "2. 경기변동", "3. 인플레이션"], "answer": 2, "news_snippet": "경기변동 사이클 상 하락 국면 진입? 전문가들 방어주 투자 권고."},
            {"question": "직장을 구하려는 의지가 있음에도 일자리를 구하지 못한 상태는?", "options": ["1. 고용", "2. 실업", "3. 은퇴"], "answer": 2, "news_snippet": "실업률 통계치 발표 쇼크, 소비 둔화 우려로 유통주 하락."},
            {"question": "개인이나 기업이 발명, 상표 등에 대해 가지는 독점적인 권리는?", "options": ["1. 소유권", "2. 지적재산권", "3. 영업권"], "answer": 2, "news_snippet": "바이오 기업, 핵심 지적재산권 승소로 주가 폭등!"},
            {"question": "시장에서 가격이 수요와 공급을 조절하는 기능을 빗댄 애덤 스미스의 말은?", "options": ["1. 보이지 않는 손", "2. 보이는 손", "3. 황금 손"], "answer": 1, "news_snippet": "정부 개입 논란, '보이지 않는 손'에 맡겨야 한다는 목소리."},
            {"question": "가계가 노동이나 자본을 제공하고 얻는 대가는?", "options": ["1. 지출", "2. 소득", "3. 부채"], "answer": 2, "news_snippet": "국민 가계 소득 증가율 둔화, 내수 시장 침체로 이어질까 촉각."},
            {"question": "일반적으로 예금 금리와 대출 금리 중 어느 것이 더 높을까요?", "options": ["1. 예금 금리", "2. 대출 금리", "3. 항상 같다"], "answer": 2, "news_snippet": "예금과 대출 금리 차이 확대로 금융주 사상 최대 실적!"},
            {"question": "정부가 경제를 살리기 위해 세금을 줄이고 지출을 늘리는 정책은?", "options": ["1. 긴축 재정", "2. 확대 재정", "3. 통화 정책"], "answer": 2, "news_snippet": "정부 대규모 확대 재정 편성, 시장에 유동성 공급 기대감."},
            {"question": "앞으로 주가가 오를 것으로 기대하는 상승장을 상징하는 동물은?", "options": ["1. 곰(Bear)", "2. 황소(Bull)", "3. 독수리(Eagle)"], "answer": 2, "news_snippet": "월가에 황소(Bull)가 돌아왔다! 증시 연일 최고점 돌파."},
            {"question": "앞으로 주가가 떨어질 것으로 예상하는 하락장을 상징하는 동물은?", "options": ["1. 곰(Bear)", "2. 황소(Bull)", "3. 사자(Lion)"], "answer": 1, "news_snippet": "베어마켓(Bear Market) 공포 확산, 투자자들 현금 확보 비상."},
            {"question": "기업이 새로 주식을 발행하여 사람들에게 처음으로 파는 과정을 뜻하는 약자는?", "options": ["1. GDP", "2. IPO", "3. M&A"], "answer": 2, "news_snippet": "하반기 최대어 기업 IPO 돌입, 공모주 청약에 수십조 쏠려."},
            {"question": "두 개 이상의 기업이 하나로 합쳐지거나 다른 기업을 사들이는 것을 뜻하는 약자는?", "options": ["1. M&A", "2. IPO", "3. CEO"], "answer": 1, "news_snippet": "빅테크 기업들의 초대형 M&A 발표! 관련주 상한가 직행."}
        ]
        random.shuffle(self.quizzes)

    def load_market_data(self):
        end_date = self.current_date + relativedelta(months=self.total_turns + 2)

        # [BUG FIX 2] yfinance 최신 버전의 MultiIndex 컬럼 구조 안정적으로 처리
        raw = yf.download(
            self.all_tickers,
            start=self.current_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            progress=False,
            auto_adjust=True   # 수정 주가(adjusted close) 사용
        )

        # yfinance 버전에 따라 컬럼 구조가 다를 수 있으므로 안전하게 처리
        if isinstance(raw.columns, pd.MultiIndex):
            # 최신 yfinance: ('Close', 'AAPL') 형태의 MultiIndex
            if 'Close' in raw.columns.get_level_values(0):
                self.market_data = raw['Close']
            elif 'Price' in raw.columns.get_level_values(0):
                self.market_data = raw['Price']
            else:
                # 첫 번째 레벨의 첫 항목 사용 (fallback)
                self.market_data = raw[raw.columns.get_level_values(0)[0]]
        else:
            # 단일 종목이거나 구버전 yfinance
            self.market_data = raw

        # DatetimeIndex가 timezone-aware인 경우 timezone 제거 (비교 오류 방지)
        if hasattr(self.market_data.index, 'tz') and self.market_data.index.tz is not None:
            self.market_data.index = self.market_data.index.tz_localize(None)

    def get_price(self, ticker, date):
        if self.market_data.empty:
            return 0.0

        date_str = date.strftime('%Y-%m-%d')

        try:
            # [BUG FIX 3] loc 슬라이싱 실패 대비 try/except 추가
            subset = self.market_data.loc[date_str:]
            if not subset.empty and ticker in subset.columns:
                valid_prices = subset[ticker].dropna()
                if not valid_prices.empty:
                    return float(valid_prices.iloc[0])
        except (KeyError, TypeError):
            pass

        return 0.0

    def buy_stock(self, team, ticker, shares):
        price = self.get_price(ticker, self.current_date)
        if price == 0:
            return False, "현재 거래할 수 없는 주식입니다."

        is_kr = ticker.endswith('.KS')
        required_money = price * shares

        if (is_kr and team.krw_balance >= required_money) or \
           (not is_kr and team.usd_balance >= required_money):
            if is_kr:
                team.krw_balance -= required_money
            else:
                team.usd_balance -= required_money

            if ticker in team.portfolio:
                old_shares = team.portfolio[ticker]['shares']
                old_avg = team.portfolio[ticker]['avg_price']
                new_shares = old_shares + shares
                new_avg = ((old_shares * old_avg) + (shares * price)) / new_shares
                team.portfolio[ticker] = {'shares': new_shares, 'avg_price': new_avg}
            else:
                team.portfolio[ticker] = {'shares': shares, 'avg_price': price}

            return True, f"[{team.name}] {ticker} {shares}주 매수 완료!"
        else:
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

        return True, f"[{team.name}] {ticker} {shares}주 매도 완료!"

    def exchange_currency(self, team, direction, amount_usd):
        exchange_rate = self.get_price('USDKRW=X', self.current_date)
        if exchange_rate == 0:
            exchange_rate = 1300.0

        if direction == 'KRW_TO_USD':
            applied_rate = exchange_rate * 1.05
            required_krw = amount_usd * applied_rate
            if team.krw_balance >= required_krw:
                team.krw_balance -= required_krw
                team.usd_balance += amount_usd
                return True, f"{amount_usd:,.0f}달러 구매 완료 (적용 환율: {applied_rate:,.2f}원)"
            return False, "원화 잔고가 부족합니다."

        elif direction == 'USD_TO_KRW':
            applied_rate = exchange_rate * 0.95
            received_krw = amount_usd * applied_rate
            if team.usd_balance >= amount_usd:
                team.usd_balance -= amount_usd
                team.krw_balance += received_krw
                return True, f"{received_krw:,.0f}원 획득 완료 (적용 환율: {applied_rate:,.2f}원)"
            return False, "달러 잔고가 부족합니다."

    def check_bankruptcy(self, team):
        initial_value = 230000000
        current_value = team.get_total_value_krw(self.get_price, self.current_date)
        if current_value < (initial_value * 0.1):
            team.is_bankrupt = True

    def next_turn(self):
        for team in self.teams:
            if not team.is_bankrupt:
                self.check_bankruptcy(team)
        self.current_turn += 1
        self.current_date += relativedelta(months=1)


# ==========================================
# 3. UI 렌더링 헬퍼 함수
# ==========================================
def display_portfolio_ui(team, get_price_func, current_date):
    if not team.portfolio:
        st.info("현재 보유 중인 주식이 없습니다.")
        return

    portfolio_data = []
    for ticker, info in team.portfolio.items():
        shares = info['shares']
        avg_price = info['avg_price']
        current_price = get_price_func(ticker, current_date)

        return_rate = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0
        currency = "KRW" if ticker.endswith('.KS') else "USD"

        avg_str = f"${avg_price:,.2f}" if currency == "USD" else f"{avg_price:,.0f}원"
        cur_str = f"${current_price:,.2f}" if currency == "USD" else f"{current_price:,.0f}원"

        portfolio_data.append({
            "종목명": ticker,
            "수량": shares,
            "평단가": avg_str,
            "현재가": cur_str,
            "수익률": f"{return_rate:+.2f}%"
        })

    df = pd.DataFrame(portfolio_data)

    # [BUG FIX 4] pandas 버전에 따라 style.applymap → style.map 변경됨
    # pandas < 2.1: applymap / pandas >= 2.1: map (applymap deprecated)
    def color_return(val):
        if '+' in val:
            return 'color: red'
        elif '-' in val:
            return 'color: blue'
        return 'color: black'

    try:
        styled_df = df.style.map(color_return, subset=['수익률'])
    except AttributeError:
        styled_df = df.style.applymap(color_return, subset=['수익률'])

    st.dataframe(styled_df, use_container_width=True, hide_index=True)


# ==========================================
# 4. Streamlit 메인 앱 로직
# ==========================================
def main():
    st.set_page_config(page_title="글로벌 모의투자 게임", layout="wide")
    st.title("글로벌 모의투자 보드게임")

    if 'game_started' not in st.session_state:
        st.session_state.game_started = False

    # --- [화면 1] 로비 화면 ---
    if not st.session_state.game_started:
        st.subheader("게임 세팅 로비")
        with st.form("lobby_form"):
            st.markdown("#### 1. 게임 기본 설정")
            col1, col2 = st.columns(2)
            total_turns = col1.slider("총 게임 길이 (턴/개월)", min_value=8, max_value=18, value=12)
            start_dates = ['random', '2001-01-01', '2005-05-01', '2010-01-01', '2015-05-01', '2020-01-01', '2023-01-01']
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

                    if st.session_state.game.quizzes:
                        st.session_state.current_quiz = st.session_state.game.quizzes.pop()
                    else:
                        st.session_state.current_quiz = None

                    st.session_state.game_started = True
                st.rerun()

    # --- [화면 2] 본 게임 화면 ---
    else:
        game = st.session_state.game

        if st.sidebar.button("게임 강제 종료 (로비로 돌아가기)"):
            st.session_state.clear()
            st.rerun()

        # 게임 종료 처리 및 브리핑
        if st.session_state.get('game_over', False) or game.current_turn > game.total_turns:
            st.header("게임이 종료되었습니다!")
            st.markdown("### 최종 결과")
            results = []
            for team in game.teams:
                final_val = team.get_total_value_krw(game.get_price, game.current_date)
                results.append((team.name, final_val))
                st.write(f"**{team.name}** 총 자산: {final_val:,.0f} 원")

            winner = max(results, key=lambda x: x[1])
            st.success(f"최종 우승팀은 **{winner[0]}** 입니다!")

            with st.expander("게임에서 배운 점 확인하기 (경제 지식 브리핑)", expanded=True):
                st.markdown("""
                * **환율 변동성(FX Risk):** 미국 주식 투자 시 환율 변동에 따른 환차손과 수수료의 중요성을 체감했습니다.
                * **거시 경제와 주식 시장:** 퀴즈를 통해 본 경제 상황이 주가에 미치는 영향을 확인했습니다.
                * **기회비용과 자산 배분:** 제한된 자본으로 현금을 보유할지, 주식에 투자할지 결정하는 모든 순간이 기회비용이었습니다.
                * **장기 투자와 복리:** 시장의 오르내림 속에서도 우량 자산을 믿고 버티는 투자의 힘을 경험했습니다.
                """)
            return

        # 턴 현황
        st.header(f"현재 턴: {game.current_turn} / {game.total_turns}")
        st.subheader(f"현재 날짜: {game.current_date.strftime('%Y-%m-%d')}")
        st.markdown("---")

        # 경제 퀴즈
        st.subheader("이번 달 경제 뉴스 퀴즈")
        if st.session_state.current_quiz:
            quiz = st.session_state.current_quiz
            if not st.session_state.quiz_answered:
                st.info("퀴즈를 맞히면 시장의 흐름을 읽을 수 있는 핵심 뉴스가 공개됩니다. (기회는 한 번!)")
                st.write(f"**Q. {quiz['question']}**")

                # [BUG FIX 5] st.radio의 index 기본값 명시 → 매 턴마다 초기화 보장
                user_choice = st.radio("정답 선택:", quiz['options'], index=0, key=f"quiz_radio_{game.current_turn}")

                if st.button("정답 제출"):
                    st.session_state.quiz_answered = True
                    selected_num = int(user_choice.split(".")[0])
                    st.session_state.news_unlocked = (selected_num == quiz['answer'])
                    st.rerun()
            else:
                if st.session_state.news_unlocked:
                    st.success(f"**[핵심 뉴스 획득]**\n\n{quiz['news_snippet']}")
                else:
                    st.error("오답입니다. 이번 달 시장 정보는 제공되지 않습니다.")
        else:
            st.write("준비된 퀴즈가 모두 소진되었습니다.")
        st.markdown("---")

        # 팀별 자산 및 거래 대시보드
        tabs = st.tabs([team.name for team in game.teams])
        for i, team in enumerate(game.teams):
            with tabs[i]:
                if team.is_bankrupt:
                    st.error("파산한 팀입니다. 자산 가치가 초기 자본의 10% 미만으로 떨어졌습니다.")
                    continue

                total_val = team.get_total_value_krw(game.get_price, game.current_date)
                st.metric("총 자산 평가액 (원)", f"{total_val:,.0f}")

                col1, col2 = st.columns(2)
                col1.metric("보유 원화 (KRW)", f"{team.krw_balance:,.0f}")
                col2.metric("보유 달러 (USD)", f"{team.usd_balance:,.2f}")

                st.markdown("##### 현재 포트폴리오")
                display_portfolio_ui(team, game.get_price, game.current_date)

                st.markdown("---")

                trade_col, exch_col = st.columns(2)

                with trade_col:
                    st.write("**주식 거래**")
                    # [BUG FIX 1 적용] USDKRW=X 제외한 tradeable_tickers만 표시
                    trade_ticker = st.selectbox(
                        "종목 선택",
                        game.tradeable_tickers,
                        key=f"ticker_{team.name}"
                    )
                    trade_shares = st.number_input(
                        "거래 수량", min_value=1, step=1,
                        key=f"shares_{team.name}"
                    )

                    t_btn1, t_btn2 = st.columns(2)
                    if t_btn1.button("매수 (Buy)", key=f"buy_{team.name}"):
                        success, msg = game.buy_stock(team, trade_ticker, trade_shares)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    if t_btn2.button("매도 (Sell)", key=f"sell_{team.name}"):
                        success, msg = game.sell_stock(team, trade_ticker, trade_shares)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)

                with exch_col:
                    st.write("**환전 (수수료 5% 적용)**")
                    exch_amount = st.number_input(
                        "환전 기준 금액 (달러)", min_value=100.0, step=100.0,
                        key=f"exch_{team.name}"
                    )

                    e_btn1, e_btn2 = st.columns(2)
                    if e_btn1.button("달러 구매", key=f"buy_usd_{team.name}"):
                        success, msg = game.exchange_currency(team, 'KRW_TO_USD', exch_amount)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    if e_btn2.button("달러 판매", key=f"sell_usd_{team.name}"):
                        success, msg = game.exchange_currency(team, 'USD_TO_KRW', exch_amount)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)

        # 턴 종료 버튼
        st.markdown("---")
        if st.button("다음 턴으로 이동 (1개월 후)"):
            game.next_turn()
            st.session_state.quiz_answered = False
            st.session_state.news_unlocked = False

            if st.session_state.game.quizzes:
                st.session_state.current_quiz = st.session_state.game.quizzes.pop()
            else:
                st.session_state.current_quiz = None

            if game.current_turn > game.total_turns:
                st.session_state.game_over = True

            st.rerun()


if __name__ == "__main__":
    main()