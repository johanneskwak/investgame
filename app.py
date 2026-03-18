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
    name = TICKER_NAMES.get(ticker, ticker)
    return f"{name} ({ticker})"

# ==========================================
# 1. 오프라인 과거 뉴스 생성기 (API 불필요)
# ==========================================
def get_mock_news(current_date):
    year = current_date.year
    
    # 연도별 굵직한 실제 경제 테마 적용
    if year <= 2002:
        news_list = ["IT 버블 붕괴 여파 지속, 기술주 실적 악화", "신흥국 증시 변동성 확대", "투자자들 안전 자산 선호 심리 강화"]
    elif year in [2008, 2009]:
        news_list = ["글로벌 금융 위기 공포 확산, 증시 패닉", "각국 중앙은행 긴급 유동성 공급 및 금리 인하", "부동산 시장 침체로 인한 실물 경제 타격 우려"]
    elif year in [2020, 2021]:
        news_list = ["전염병 팬데믹 선언, 글로벌 공급망 마비", "비대면(언택트), 바이오 관련 기술주 테마 급등", "각국 전례 없는 양적 완화 정책으로 유동성 폭발"]
    elif year >= 2022:
        news_list = ["글로벌 인플레이션 압력 심화, 미 연준 금리 인상 기조", "원자재 및 에너지 가격 폭등으로 기업 비용 부담 증가", "환율 변동성 극대화, 수출 기업 단기 실적 변수"]
    else:
        # 일반적인 경제 뉴스 풀
        news_list = [
            random.choice(["주요국 중앙은행 금리 동결 시사, 시장 안도감", "외국인 투자자, 아시아 신흥국 우량주 매수세 유입", "글로벌 거시 경제 지표 혼조세, 관망 심리 뚜렷"]),
            random.choice(["반도체·IT 업종 하반기 실적 호조 기대감", "유가 등 에너지 가격 상승으로 인한 소비 위축 우려", "달러 환율 변동성 확대, 수출 기업과 수입 기업 희비 교차"]),
            random.choice(["기관 투자자 포트폴리오 재편 움직임 포착", "친환경·신재생 에너지 관련주 정부 정책 수혜 기대", "내수 소비 심리 점진적 회복세 전환 조짐"])
        ]
    
    return "\n\n".join([f"📌 {news}" for news in news_list])


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

        self.start_dates_pool = ['2001-01-01', '2005-05-01', '2010-01-01', '2015-05-01', '2020-01-01', '2023-01-01']
        chosen_date = start_date_choice if start_date_choice in self.start_dates_pool else random.choice(self.start_dates_pool)
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
        if
