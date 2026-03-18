import streamlit as st
import pandas as pd
import yfinance as yf
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ==========================================
# 0. 종목 한글명 매핑
# ==========================================
TICKER_NAMES = {
    'AAPL': '애플', 'MSFT': '마이크로소프트', 'GOOGL': '구글(알파벳)', 'AMZN': '아마존',
    'NVDA': '엔비디아', 'TSLA': '테슬라', 'META': '메타(페이스북)', 'NFLX': '넷플릭스',
    'AMD': 'AMD', 'INTC': '인텔', 'DIS': '디즈니', 'SBUX': '스타벅스',
    'NKE': '나이키', 'KO': '코카콜라', 'PEP': '펩시', 'MCD': '맥도날드',
    'WMT': '월마트', 'BA': '보잉', 'JPM': 'JP모건', 'V': '비자',
    'GME': '게임스탑', 'AMC': 'AMC엔터테인먼트', 'PLTR': '팔란티어', 'COIN': '코인베이스',
    'RBLX': '로블록스', 'UBER': '우버', 'ABNB': '에어비앤비', 'PFE': '화이자',
    'MRNA': '모더나', 'MA': '마스터카드',
    '005930.KS': '삼성전자', '000660.KS': 'SK하이닉스', '373220.KS': 'LG에너지솔루션',
    '207940.KS': '삼성바이오로직스', '005380.KS': '현대차', '035420.KS': 'NAVER',
    '035720.KS': '카카오', '051910.KS': 'LG화학', '000270.KS': '기아',
    '068270.KS': '셀트리온', '005490.KS': 'POSCO홀딩스', '105560.KS': 'KB금융',
    '028260.KS': '삼성물산', '012330.KS': '현대모비스', '066570.KS': 'LG전자',
    '036570.KS': 'NC소프트', '259960.KS': '크래프톤', '352820.KS': '하이브',
    '011200.KS': 'HMM(현대상선)', '096770.KS': 'SK이노베이션',
    '034730.KS': 'SK(주)', '010130.KS': '고려아연', '316140.KS': '우리금융',
    '024110.KS': '기업은행', '032830.KS': '삼성생명', '090430.KS': '아모레퍼시픽',
    '009150.KS': '삼성전기', '042700.KS': '한미반도체', '010950.KS': 'S-Oil',
    '018260.KS': '삼성SDS',
}


def ticker_label(ticker: str) -> str:
    name = TICKER_NAMES.get(ticker, ticker)
    return f"{name} ({ticker})"


def safe_key(s: str) -> str:
    """위젯 key에 사용 불가한 특수문자 제거"""
    for ch in ['.', '=', ' ', '-', '(', ')', '/']:
        s = s.replace(ch, '_')
    return s


# ==========================================
# 1. 내장 경제 뉴스 DB (API 불필요)
# ==========================================
NEWS_DB = {
    (2001, 1):  ["📌 美 Fed 기준금리 0.5%p 전격 인하 — 경기침체 우려 대응",
                 "📌 나스닥 IT버블 붕괴 여파 지속 — 추가 하락 경고",
                 "📌 삼성전자, D램 가격 하락에도 반도체 설비 투자 확대 발표",
                 "📌 일본 제로금리 정책 재확인 — 엔화 약세 지속",
                 "📌 국내 IT기업 구조조정 가속 — 코스닥 연일 신저가"],
    (2001, 2):  ["📌 美 Fed 추가 금리 인하 5.5%→5.0% — 증시 단기 반등",
                 "📌 엔론 회계 부정 의혹 초기 보도 — 에너지주 경계감",
                 "📌 현대차, 미국 시장 점유율 확대 전략 발표",
                 "📌 하이닉스 D램 가격 하락 — 유동성 위기 우려",
                 "📌 국내 카드사 현금서비스 과도 대출 문제 수면 위로"],
    (2001, 3):  ["📌 나스닥 1년간 -60% 폭락 — IT버블 붕괴 공식 확인",
                 "📌 일본 닛케이 16년 만에 최저 — 아시아 증시 동반 하락",
                 "📌 삼성전자 1분기 영업이익 전년 대비 -70% 예고",
                 "📌 한국은행 기준금리 인하 가능성 시사",
                 "📌 SK텔레콤·KT 3G 투자 계획 발표 — 통신주 관심"],
    (2001, 9):  ["📌 ⚠️ 9·11 테러 발생 — 글로벌 증시 사상 최대 폭락",
                 "📌 뉴욕증시 주간 하락폭 역대 최대 — 항공·보험주 직격탄",
                 "📌 Fed 긴급 금리 인하, 유동성 공급 총력",
                 "📌 원/달러 환율 급등 — 외국인 국내 증시 대거 이탈",
                 "📌 삼성전자·SK하이닉스 반도체 수요 급감 우려"],
    (2001, 11): ["📌 엔론 파산 신청 — 미국 역사상 최대 기업 파산",
                 "📌 애플 아이팟(iPod) 최초 출시 — 소비전자 시장 패러다임 변화",
                 "📌 항공·여행업계 구조조정 가속화",
                 "📌 한국 수출 소폭 회복 — 반도체·자동차 주도",
                 "📌 현대차 해외 판매 증가, 실적 개선 기대"],
    (2005, 1):  ["📌 美 Fed 기준금리 2.25%→2.5% 인상 — 긴축 사이클 지속",
                 "📌 국제유가 배럴당 45달러 돌파 — 에너지·정유주 강세",
                 "📌 삼성전자 반도체·LCD 동시 호황 — 역대 최대 실적 전망",
                 "📌 현대차 미국 J.D.Power 품질 조사 1위 — 점유율 상승",
                 "📌 코스피 1,000선 회복 눈앞 — 외국인 순매수 전환"],
    (2005, 5):  ["📌 美 장기금리 하락 — 경기 과열 우려 완화",
                 "📌 마이크로소프트 Xbox 360 출시 예고 — 게임·반도체 수혜",
                 "📌 LG화학, 2차전지 대규모 투자 발표",
                 "📌 코스피 1,100선 돌파 성공 — IT·금융주 동반 상승",
                 "📌 POSCO, 중국 합작 제철소 착공 — 해외 사업 확대"],
    (2010, 1):  ["📌 美 오바마, 은행 '대마불사' 방지 금융규제 추진",
                 "📌 중국 GDP 일본 제치고 세계 2위 확실시",
                 "📌 삼성전자 갤럭시S 출시 예고 — 애플과 스마트폰 경쟁 선언",
                 "📌 현대차 2009년 글로벌 판매 320만대 — 역대 최고 점유율",
                 "📌 코스피 1,700선 돌파 — 외국인 연속 순매수"],
    (2010, 2):  ["📌 그리스 국가부채 위기 심화 — 유로존 재정 불안 확산",
                 "📌 애플 아이패드 공개 — 태블릿 시장 탄생",
                 "📌 美 Fed 재할인율 0.25%p 인상 — 출구전략 서막",
                 "📌 하이닉스 D램 흑자 전환 확인 — 반도체 업황 회복",
                 "📌 POSCO·현대제철 자동차 강판 가격 인상 협상"],
    (2010, 5):  ["📌 유로존 재정위기 전면화 — 코스피 100포인트 급락",
                 "📌 천안함 피격 사건 — 지정학 리스크로 원화 급락",
                 "📌 美 도드-프랭크 금융개혁법 심의 — 은행주 약세",
                 "📌 삼성전자 낸드플래시 감산 검토",
                 "📌 외국인 국내 증시 대규모 순매도"],
    (2010, 9):  ["📌 美 Fed QE2(2차 양적완화) 공식화 — 글로벌 유동성 급증",
                 "📌 삼성전자 반도체·스마트폰 동시 호황",
                 "📌 LG화학 전기차 배터리 GM 수주 확대",
                 "📌 코스피 1,900선 돌파 — 사상 첫 도전",
                 "📌 중국 위안화 절상 압박 증가 — 신흥국 자본 유입 급증"],
    (2015, 1):  ["📌 유럽중앙은행(ECB), 1조 유로 양적완화 전격 발표",
                 "📌 스위스 프랑화 페그제 폐지 — 글로벌 환율 충격",
                 "📌 삼성전자 갤럭시S6 출시 일정 공개 — 메탈 디자인 기대",
                 "📌 국제유가 WTI 50달러 붕괴 — 에너지주 급락",
                 "📌 코스피, 외국인 순매수 전환 — 2,100선 회복 시도"],
    (2015, 5):  ["📌 메르스(MERS) 확산 — 내수·유통·여행주 급락",
                 "📌 중국 증시 5,000선 돌파 — 버블 경고음",
                 "📌 현대차 메르스 영향 생산·판매 지장 우려",
                 "📌 카카오, 모바일 결제 '카카오페이' 성장 가속",
                 "📌 코스피 메르스 쇼크로 단기 -2% 급락"],
    (2020, 1):  ["📌 중국 우한 코로나19 발생 초기 보고 — 글로벌 경계감 고조",
                 "📌 美-中 1단계 무역합의 서명 — 무역분쟁 일단락",
                 "📌 테슬라 주가 월간 +40% 급등 — 전기차 투자 열풍",
                 "📌 삼성전자 반도체·스마트폰 실적 호조 전망",
                 "📌 코스피 2,250 수준, 외국인 순매수 기조"],
    (2020, 2):  ["📌 코로나19 이탈리아·한국 급속 확산 — 글로벌 패닉셀",
                 "📌 美 S&P500 2주간 -10% — 2008년 이후 최대 낙폭",
                 "📌 원유 수요 급감 우려 — WTI 50달러 붕괴",
                 "📌 코스피 -8% 폭락, 원/달러 환율 1,220원 돌파",
                 "📌 삼성전자 구미 공장 일시 가동 중단"],
    (2020, 3):  ["📌 WHO 코로나19 팬데믹 선언 — 글로벌 증시 역대급 폭락",
                 "📌 Fed 기준금리 0~0.25%로 긴급 인하, 무제한 양적완화",
                 "📌 코스피 1,450선 붕괴, 원/달러 1,290원 돌파",
                 "📌 뉴욕 서킷브레이커 발동 — 역사적 폭락",
                 "📌 국내 긴급 재난지원금 논의 시작"],
    (2020, 4):  ["📌 美 의회 2.2조달러 경기부양책 통과 — 증시 반등",
                 "📌 WTI 유가 사상 첫 마이너스(-37달러) 기록",
                 "📌 아마존·넷플릭스 비대면 수요 폭발 — 사상 최고가",
                 "📌 삼성전자 1분기 반도체 수요 견조 — 선방 실적",
                 "📌 코스피 2,000선 회복 — 부양책 효과"],
    (2020, 8):  ["📌 美 Fed 평균물가목표제(AIT) 도입 — 저금리 장기화 선언",
                 "📌 애플 주식 분할(4:1) — 다우지수 편입",
                 "📌 코스피 2,400선 돌파 — 개인 투자자 열풍",
                 "📌 삼성바이오로직스·셀트리온 코로나 치료제 기대감",
                 "📌 NAVER·카카오 시가총액 30조원 돌파"],
    (2023, 1):  ["📌 美 인플레이션 둔화 신호 — Fed 금리 인상 속도 조절 기대",
                 "📌 테슬라 가격 20% 인하 — 전기차 가격 전쟁 시작",
                 "📌 삼성전자 4분기 영업이익 -69% 급감 — 반도체 불황 확인",
                 "📌 ChatGPT 열풍 — AI 관련주 전 세계 폭등",
                 "📌 코스피 2,400선 회복 시도 — 중국 리오프닝 기대"],
    (2023, 2):  ["📌 美 1월 고용 51만명 증가 — 예상치 3배, 금리 인상 장기화 우려",
                 "📌 구글 AI 챗봇 '바드' 시연 오류 — 알파벳 주가 급락",
                 "📌 마이크로소프트 AI 검색 '코파일럿' 선제 공개 — 시총 급등",
                 "📌 엔비디아 실적 호조 — AI 반도체 수요 폭발",
                 "📌 원/달러 환율 1,290원 재돌파 — 외국인 순매도"],
    (2023, 3):  ["📌 실리콘밸리뱅크(SVB) 파산 — 미국 역대 2번째 대형 은행 도산",
                 "📌 크레디스위스 위기 — UBS 전격 인수",
                 "📌 삼성전자 반도체 자발적 감산 결정 발표",
                 "📌 Fed 금리 인상 vs 금융 안정 딜레마",
                 "📌 코스피 금융 불안으로 2,400선 붕괴"],
    (2023, 5):  ["📌 엔비디아 실적 전망 폭발 — AI 반도체 매출 3배 예고",
                 "📌 에코프로·포스코퓨처엠 2차전지 소재주 연일 상한가",
                 "📌 美 부채한도 협상 교착 — 기술적 디폴트 우려",
                 "📌 LG에너지솔루션 미국 IRA 보조금 수혜 확정",
                 "📌 코스피 2,600선 돌파 — 2차전지·AI 쌍끌이"],
    (2023, 6):  ["📌 엔비디아 시총 1조달러 돌파 — AI 반도체 황금기",
                 "📌 美 부채한도 타결 — 디폴트 방지",
                 "📌 Fed '매파적 동결' — 추가 인상 시사",
                 "📌 한국 2차전지 거품 논란 — 에코프로 단기 급락 후 재반등",
                 "📌 코스피 2,600선 공방"],
    (2023, 10): ["📌 이스라엘·하마스 전쟁 발발 — 지정학 리스크 급부상",
                 "📌 美 국채 금리 5% 돌파 — 2007년 이후 최고",
                 "📌 삼성전자 3분기 영업이익 바닥 확인 — 반등 기대",
                 "📌 유가 배럴당 95달러 — 에너지주 강세",
                 "📌 코스피 2,300선 붕괴 — 외국인 대규모 매도"],
    (2023, 11): ["📌 美 Fed 2회 연속 금리 동결 — 금리 인상 종료 확실시",
                 "📌 오픈AI CEO 샘 알트만 해임·복귀 사태 — AI 업계 충격",
                 "📌 엔비디아 3분기 매출 전년 대비 +206% 성장 확인",
                 "📌 삼성전자·SK하이닉스 반도체 가격 반등 확인",
                 "📌 코스피 2,500선 회복 — 외국인 순매수 전환"],
    (2023, 12): ["📌 美 Fed 2024년 금리 인하 3회 전망 — 증시 연말 랠리",
                 "📌 나스닥 2023년 연간 +43% — AI 열풍이 이끈 역대급 한 해",
                 "📌 삼성전자 HBM3·HBM3E 대규모 공급 계약 임박",
                 "📌 2차전지 소재주 연말 조정 — 전기차 수요 둔화 우려",
                 "📌 코스피 연간 +18%, 외국인 순매수 27조원 역대 최대"],
    (2024, 1):  ["📌 비트코인 현물 ETF 美 SEC 승인 — 암호화폐 급등",
                 "📌 테슬라 4분기 인도량 예상치 하회 — 주가 급락",
                 "📌 삼성전자 HBM3E 엔비디아 납품 최종 승인 임박",
                 "📌 美 CPI 예상 상회 — 3월 금리 인하 기대 후퇴",
                 "📌 코스피 저PBR주 밸류업 프로그램 기대 — 강세"],
    (2024, 2):  ["📌 엔비디아 4분기 실적 전망치 3배 상회 — AI 반도체 슈퍼 사이클",
                 "📌 일본 닛케이 34년 만에 사상 최고치 돌파",
                 "📌 美 1월 CPI 3.1% — 금리 인하 시기 6월로 후퇴",
                 "📌 삼성전자 주주환원 확대 및 HBM 투자 발표",
                 "📌 코스피 2,650선 — 외국인 반도체 순매수"],
    (2024, 4):  ["📌 이란·이스라엘 상호 공격 — 중동 지정학 리스크 최고조",
                 "📌 美 CPI 3.5% 재상승 — 금리 인하 연기 우려",
                 "📌 삼성전자 1분기 영업이익 6.6조원 — 반도체 부활 확인",
                 "📌 원/달러 환율 1,400원 돌파 — 15년 만에 최고치",
                 "📌 나스닥 월간 -4% — AI 고평가 조정"],
    (2024, 6):  ["📌 엔비디아 시총 3조달러 돌파 — 세계 시총 1위 등극",
                 "📌 美 Fed 6월 금리 동결, 연내 인하 1회로 축소",
                 "📌 삼성전자 파운드리 AMD·엔비디아 추가 수주 기대",
                 "📌 SK하이닉스 HBM 시장 점유율 50% 상회",
                 "📌 코스피 2,800선 돌파 — 외국인 반도체 대규모 매수"],
}


def get_news(year: int, month: int) -> str:
    """DB에 있으면 반환, 없으면 시대 맥락 반영 일반 뉴스 생성"""
    if (year, month) in NEWS_DB:
        return "\n\n".join(NEWS_DB[(year, month)])

    pool = [
        f"📌 {year}년 {month}월, 주요국 중앙은행 통화정책 방향에 글로벌 증시 촉각",
        "📌 국제유가 변동성 확대 — 에너지주 및 항공·해운주 주목",
        "📌 원/달러 환율 등락 — 수출주 수익성 변동 예고",
        "📌 미국 고용·소비 지표 발표 예정 — 경기 방향성 분수령",
        "📌 국내 기업 실적 발표 시즌 — 반도체·자동차·2차전지 업황 관심",
        "📌 중국 경기 회복 속도 둔화 우려 — 대중 수출 기업 주의",
        "📌 한국은행 금통위 기준금리 결정 예정 — 동결 여부 주목",
        "📌 글로벌 공급망 재편 가속 — 소재·부품·장비주 수혜 기대",
    ]
    if month in (1, 2):
        pool.append("📌 연초 기관 포트폴리오 리밸런싱 — 주도 섹터 교체 가능성")
    elif month in (3, 4, 5):
        pool.append("📌 1분기 실적 발표 시즌 개막 — 어닝 서프라이즈 종목 발굴 관심")
    elif month in (6, 7, 8):
        pool.append("📌 상반기 결산 시즌 — 배당주 및 가치주 관심 증가")
    elif month in (9, 10, 11):
        pool.append("📌 3분기 실적 발표 시즌 — 연말 랠리 기대감 선반영")
    else:
        pool.append("📌 연말 윈도드레싱 — 기관 포트폴리오 마무리 매수 가능성")

    return "\n\n".join(random.sample(pool, min(5, len(pool))))


# ==========================================
# 2. 팀 클래스
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
        rate = get_price_func('USDKRW=X', current_date) or 1300
        total = self.krw_balance + self.usd_balance * rate
        for ticker, info in self.portfolio.items():
            price = get_price_func(ticker, current_date)
            shares = info['shares']
            total += price * shares if ticker.endswith('.KS') else price * shares * rate
        return total


# ==========================================
# 3. 게임 클래스
# ==========================================
class MockInvestmentGame:
    def __init__(self, team_names, total_turns=12, start_date_choice='random'):
        self.total_turns = total_turns
        self.current_turn = 1
        self.teams = [Team(n) for n in team_names]

        pool = ['2001-01-01', '2005-05-01', '2010-01-01',
                '2015-05-01', '2020-01-01', '2023-01-01']
        chosen = start_date_choice if start_date_choice in pool else random.choice(pool)
        self.current_date = datetime.strptime(chosen, '%Y-%m-%d')

        self.us_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX',
            'AMD', 'INTC', 'DIS', 'SBUX', 'NKE', 'KO', 'PEP', 'MCD', 'WMT',
            'BA', 'JPM', 'V', 'GME', 'AMC', 'PLTR', 'COIN', 'RBLX', 'UBER',
            'ABNB', 'PFE', 'MRNA', 'MA',
        ]
        self.kr_tickers = [
            '005930.KS', '000660.KS', '373220.KS', '207940.KS', '005380.KS',
            '035420.KS', '035720.KS', '051910.KS', '000270.KS', '068270.KS',
            '005490.KS', '105560.KS', '028260.KS', '012330.KS', '066570.KS',
            '036570.KS', '259960.KS', '352820.KS', '011200.KS', '096770.KS',
            '034730.KS', '010130.KS', '316140.KS', '024110.KS', '032830.KS',
            '090430.KS', '009150.KS', '042700.KS', '010950.KS', '018260.KS',
        ]
        self.tradeable_tickers = self.us_tickers + self.kr_tickers
        self.all_tickers = self.tradeable_tickers + ['USDKRW=X']
        self.market_data = pd.DataFrame()

        self.quizzes = [
            {"question": "선택으로 인해 포기해야 하는 대안 중 가장 가치 있는 것은?",
             "options": ["1. 매몰비용", "2. 기회비용", "3. 한계비용"], "answer": 2},
            {"question": "사람들의 욕망은 무한하지만 자원은 한정된 상태는?",
             "options": ["1. 희소성", "2. 효율성", "3. 형평성"], "answer": 1},
            {"question": "가격이 오르면 수요량은 어떻게 될까요?",
             "options": ["1. 증가한다", "2. 감소한다", "3. 변동 없다"], "answer": 2},
            {"question": "콜라와 사이다처럼 한 재화 가격 상승 시 다른 재화 수요가 늘어나는 관계는?",
             "options": ["1. 보완재", "2. 정상재", "3. 대체재"], "answer": 3},
            {"question": "스마트폰과 충전기처럼 함께 소비할 때 만족감이 커지는 재화는?",
             "options": ["1. 보완재", "2. 대체재", "3. 열등재"], "answer": 1},
            {"question": "수요량과 공급량이 일치하여 결정되는 가격은?",
             "options": ["1. 최고가격", "2. 균형가격", "3. 최저가격"], "answer": 2},
            {"question": "물가가 지속적으로 오르고 화폐 가치가 떨어지는 현상은?",
             "options": ["1. 디플레이션", "2. 스태그플레이션", "3. 인플레이션"], "answer": 3},
            {"question": "인플레이션 시 유리한 사람은?",
             "options": ["1. 현금 보유자", "2. 돈을 빌린 사람", "3. 돈을 빌려준 사람"], "answer": 2},
            {"question": "물가가 지속적으로 하락하며 경제가 침체되는 현상은?",
             "options": ["1. 인플레이션", "2. 디플레이션", "3. 리디노미네이션"], "answer": 2},
            {"question": "중앙은행이 통화량을 줄이려 할 때 취할 행동은?",
             "options": ["1. 기준금리 인상", "2. 기준금리 인하", "3. 세금 감면"], "answer": 1},
            {"question": "외국 화폐에 대한 자국 화폐의 교환 비율은?",
             "options": ["1. 금리", "2. 물가", "3. 환율"], "answer": 3},
            {"question": "원/달러 환율이 올랐을 때 유리한 사람은?",
             "options": ["1. 해외 여행객", "2. 수입업자", "3. 수출업자"], "answer": 3},
            {"question": "원/달러 환율이 떨어졌을 때 피해를 볼 사람은?",
             "options": ["1. 유학생 부모", "2. 부품 수입 기업", "3. 수출 기업"], "answer": 3},
            {"question": "일정 기간 국내에서 새로 생산된 최종 생산물의 가치 합은?",
             "options": ["1. 물가지수", "2. 국내총생산(GDP)", "3. 국민총소득(GNI)"], "answer": 2},
            {"question": "소득이 많을수록 높은 세율을 적용하는 제도는?",
             "options": ["1. 비례세", "2. 누진세", "3. 역진세"], "answer": 2},
            {"question": "납세자와 담세자가 다른 세금은?",
             "options": ["1. 간접세", "2. 직접세", "3. 소득세"], "answer": 1},
            {"question": "한 기업이 시장을 장악해 가격을 결정하는 시장은?",
             "options": ["1. 완전경쟁시장", "2. 독점시장", "3. 과점시장"], "answer": 2},
            {"question": "소수 기업이 시장을 지배하는 시장은?",
             "options": ["1. 독점시장", "2. 과점시장", "3. 완전경쟁시장"], "answer": 2},
            {"question": "국방처럼 돈을 내지 않은 사람도 이용할 수 있는 재화는?",
             "options": ["1. 사유재", "2. 공공재", "3. 대체재"], "answer": 2},
            {"question": "더 적은 기회비용으로 생산 가능한 상품에 집중하는 원리는?",
             "options": ["1. 절대우위", "2. 보호무역", "3. 비교우위"], "answer": 3},
            {"question": "수입품에 높은 관세를 부과해 자국 산업을 보호하는 정책은?",
             "options": ["1. 자유무역", "2. 보호무역", "3. 공정무역"], "answer": 2},
            {"question": "원금과 이자에 또 이자가 붙는 계산 방식은?",
             "options": ["1. 단리", "2. 복리", "3. 마이너스 금리"], "answer": 2},
            {"question": "기업이 이익의 일부를 주주에게 나눠주는 돈은?",
             "options": ["1. 이자", "2. 배당금", "3. 세금"], "answer": 2},
            {"question": "경제 상태가 호황과 침체를 반복하는 현상은?",
             "options": ["1. 경제성장", "2. 경기변동", "3. 인플레이션"], "answer": 2},
            {"question": "일할 의지가 있지만 일자리를 구하지 못한 상태는?",
             "options": ["1. 고용", "2. 실업", "3. 은퇴"], "answer": 2},
            {"question": "발명·상표 등에 대한 독점적 권리는?",
             "options": ["1. 소유권", "2. 지적재산권", "3. 영업권"], "answer": 2},
            {"question": "시장에서 가격이 수급을 조절하는 기능을 빗댄 말은?",
             "options": ["1. 보이지 않는 손", "2. 보이는 손", "3. 황금 손"], "answer": 1},
            {"question": "일반적으로 예금 금리와 대출 금리 중 더 높은 것은?",
             "options": ["1. 예금 금리", "2. 대출 금리", "3. 항상 같다"], "answer": 2},
            {"question": "정부가 세금을 줄이고 지출을 늘려 경제를 살리는 정책은?",
             "options": ["1. 긴축 재정", "2. 확대 재정", "3. 통화 정책"], "answer": 2},
            {"question": "상승장을 상징하는 동물은?",
             "options": ["1. 곰(Bear)", "2. 황소(Bull)", "3. 독수리(Eagle)"], "answer": 2},
            {"question": "하락장을 상징하는 동물은?",
             "options": ["1. 곰(Bear)", "2. 황소(Bull)", "3. 사자(Lion)"], "answer": 1},
            {"question": "기업이 처음으로 주식을 공개 발행하는 과정의 약자는?",
             "options": ["1. GDP", "2. IPO", "3. M&A"], "answer": 2},
            {"question": "기업 합병·인수를 뜻하는 약자는?",
             "options": ["1. M&A", "2. IPO", "3. CEO"], "answer": 1},
        ]
        random.shuffle(self.quizzes)

    def load_market_data(self):
        end_date = self.current_date + relativedelta(months=self.total_turns + 2)
        raw = yf.download(
            self.all_tickers,
            start=self.current_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            progress=False,
            auto_adjust=True,
        )
        if isinstance(raw.columns, pd.MultiIndex):
            lv = raw.columns.get_level_values(0)
            key = 'Close' if 'Close' in lv else ('Price' if 'Price' in lv else lv[0])
            self.market_data = raw[key]
        else:
            self.market_data = raw
        if getattr(self.market_data.index, 'tz', None):
            self.market_data.index = self.market_data.index.tz_localize(None)

    def get_price(self, ticker, date):
        if self.market_data.empty:
            return 0.0
        try:
            sub = self.market_data.loc[date.strftime('%Y-%m-%d'):]
            if not sub.empty and ticker in sub.columns:
                v = sub[ticker].dropna()
                if not v.empty:
                    return float(v.iloc[0])
        except Exception:
            pass
        return 0.0

    def buy_stock(self, team, ticker, shares):
        price = self.get_price(ticker, self.current_date)
        if price == 0:
            return False, "현재 거래할 수 없는 주식입니다."
        is_kr = ticker.endswith('.KS')
        cost = price * shares
        bal = team.krw_balance if is_kr else team.usd_balance
        if bal < cost:
            return False, "잔고가 부족합니다."
        if is_kr:
            team.krw_balance -= cost
        else:
            team.usd_balance -= cost
        if ticker in team.portfolio:
            s0 = team.portfolio[ticker]['shares']
            a0 = team.portfolio[ticker]['avg_price']
            s1 = s0 + shares
            team.portfolio[ticker] = {'shares': s1, 'avg_price': (s0 * a0 + shares * price) / s1}
        else:
            team.portfolio[ticker] = {'shares': shares, 'avg_price': price}
        return True, f"{ticker_label(ticker)} {shares}주 매수 완료!"

    def sell_stock(self, team, ticker, shares):
        held = team.portfolio.get(ticker, {}).get('shares', 0)
        if held < shares:
            return False, "보유 수량이 부족합니다."
        price = self.get_price(ticker, self.current_date)
        team.portfolio[ticker]['shares'] -= shares
        if team.portfolio[ticker]['shares'] == 0:
            del team.portfolio[ticker]
        if ticker.endswith('.KS'):
            team.krw_balance += price * shares
        else:
            team.usd_balance += price * shares
        return True, f"{ticker_label(ticker)} {shares}주 매도 완료!"

    def exchange_currency(self, team, direction, amount_usd):
        rate = self.get_price('USDKRW=X', self.current_date) or 1300.0
        if direction == 'KRW_TO_USD':
            applied = rate * 1.05
            need = amount_usd * applied
            if team.krw_balance < need:
                return False, "원화 잔고가 부족합니다."
            team.krw_balance -= need
            team.usd_balance += amount_usd
            return True, f"{amount_usd:,.0f}달러 매수 완료 (적용환율 {applied:,.2f}원)"
        else:
            applied = rate * 0.95
            if team.usd_balance < amount_usd:
                return False, "달러 잔고가 부족합니다."
            team.usd_balance -= amount_usd
            team.krw_balance += amount_usd * applied
            return True, f"{amount_usd * applied:,.0f}원 획득 완료 (적용환율 {applied:,.2f}원)"

    def check_bankruptcy(self, team):
        if team.get_total_value_krw(self.get_price, self.current_date) < 23_000_000:
            team.is_bankrupt = True

    def next_turn(self):
        for t in self.teams:
            if not t.is_bankrupt:
                self.check_bankruptcy(t)
        self.current_turn += 1
        self.current_date += relativedelta(months=1)


# ==========================================
# 4. UI 헬퍼
# ==========================================
def show_portfolio(team, get_price_func, current_date):
    if not team.portfolio:
        st.info("보유 중인 주식이 없습니다.")
        return
    rows = []
    for ticker, info in team.portfolio.items():
        avg = info['avg_price']
        cur = get_price_func(ticker, current_date)
        ret = (cur - avg) / avg * 100 if avg > 0 else 0
        kr = ticker.endswith('.KS')
        rows.append({
            "종목명": ticker_label(ticker),
            "수량": info['shares'],
            "평단가": f"{avg:,.0f}원" if kr else f"${avg:,.2f}",
            "현재가": f"{cur:,.0f}원" if kr else f"${cur:,.2f}",
            "수익률": f"{ret:+.2f}%",
        })
    df = pd.DataFrame(rows)

    def color_ret(v):
        return 'color:red' if '+' in v else ('color:blue' if '-' in v else '')

    try:
        st.dataframe(df.style.map(color_ret, subset=['수익률']),
                     use_container_width=True, hide_index=True)
    except AttributeError:
        st.dataframe(df.style.applymap(color_ret, subset=['수익률']),
                     use_container_width=True, hide_index=True)


def show_fx_box(rate: float):
    if rate > 0:
        st.info(
            f"💱 **현재 환율: {rate:,.2f} 원/달러**  \n"
            f"달러 매수 적용가 **{rate*1.05:,.2f}원** (+5%) │ "
            f"달러 매도 적용가 **{rate*0.95:,.2f}원** (-5%)"
        )
    else:
        st.warning("환율 데이터 없음 — 기본값 1,300원 적용")


def quantity_input(label, key, max_val):
    """
    슬라이더 오류(min==max) 완전 방지:
    항상 number_input 사용, max_val 기준으로 step 자동 설정
    """
    max_val = max(1, int(max_val))
    if max_val >= 10000:
        step = 100
    elif max_val >= 1000:
        step = 10
    elif max_val >= 100:
        step = 5
    else:
        step = 1
    return st.number_input(
        label, min_value=1, max_value=max_val,
        value=1, step=step, key=key,
    )


# ==========================================
# 5. 메인 앱
# ==========================================
def main():
    st.set_page_config(page_title="글로벌 모의투자 게임", layout="wide")
    st.title("🌐 글로벌 모의투자 보드게임")

    if 'game_started' not in st.session_state:
        st.session_state.game_started = False

    # ── 로비 ─────────────────────────────────────────────
    if not st.session_state.game_started:
        st.subheader("게임 세팅 로비")
        with st.form("lobby_form"):
            st.markdown("#### 1. 기본 설정")
            c1, c2 = st.columns(2)
            total_turns = c1.slider("총 게임 길이 (개월)", min_value=8, max_value=18, value=12)
            start_date_choice = c2.selectbox("시작 시점", [
                'random', '2001-01-01', '2005-05-01', '2010-01-01',
                '2015-05-01', '2020-01-01', '2023-01-01',
            ])
            st.markdown("#### 2. 팀 설정")
            n_teams = st.number_input("팀 수", min_value=1, max_value=4, value=2)
            team_names = [st.text_input(f"팀 {i+1} 이름", value=f"Team {i+1}") for i in range(int(n_teams))]

            if st.form_submit_button("게임 시작하기"):
                with st.spinner("과거 주식 데이터를 불러오는 중... (최대 1~2분)"):
                    game = MockInvestmentGame(team_names, total_turns, start_date_choice)
                    game.load_market_data()
                    st.session_state.game = game
                    st.session_state.game_over = False
                    st.session_state.quiz_answered = False
                    st.session_state.news_unlocked = False
                    st.session_state.current_quiz = game.quizzes.pop() if game.quizzes else None
                    st.session_state.game_started = True
                st.rerun()
        return

    # ── 본 게임 ───────────────────────────────────────────
    game = st.session_state.game

    with st.sidebar:
        st.markdown("### ⚙️ 메뉴")
        if st.button("게임 종료 (로비로)"):
            st.session_state.clear()
            st.rerun()

    # 종료 화면
    if st.session_state.get('game_over', False) or game.current_turn > game.total_turns:
        st.header("🏁 게임 종료!")
        results = [(t.name, t.get_total_value_krw(game.get_price, game.current_date)) for t in game.teams]
        for name, val in results:
            st.write(f"**{name}** — 최종 자산: {val:,.0f} 원")
        winner = max(results, key=lambda x: x[1])
        st.success(f"🥇 우승: **{winner[0]}**")
        with st.expander("이번 게임에서 배운 점", expanded=True):
            st.markdown("""
            - **환율 리스크**: 미국 주식은 환율 변동에 따라 수익률이 크게 달라집니다.
            - **금리와 주가**: 금리 인상 시 성장주 하락, 가치주·배당주 상대적 강세.
            - **기회비용**: 현금 보유도 기회비용입니다. 최적 자산 배분이 핵심.
            - **복리의 힘**: 장기 투자와 재투자는 수익을 기하급수적으로 키웁니다.
            """)
        return

    # 턴 헤더
    d = game.current_date
    st.header(f"턴 {game.current_turn} / {game.total_turns}  —  {d.year}년 {d.month}월")
    st.markdown("---")

    # ── 퀴즈 & 뉴스 ──────────────────────────────────────
    st.subheader("📰 이번 달 경제 퀴즈 & 뉴스")
    quiz = st.session_state.current_quiz

    if quiz:
        if not st.session_state.quiz_answered:
            st.info("퀴즈를 맞히면 이번 달 핵심 경제 뉴스가 공개됩니다!")
            st.write(f"**Q. {quiz['question']}**")
            choice = st.radio("정답:", quiz['options'], index=0,
                              key=f"quiz_{game.current_turn}")
            if st.button("제출"):
                st.session_state.quiz_answered = True
                st.session_state.news_unlocked = (int(choice.split(".")[0]) == quiz['answer'])
                st.rerun()
        else:
            if st.session_state.news_unlocked:
                st.success(f"🎉 정답! — {d.year}년 {d.month}월 주요 경제 뉴스")
                st.markdown(get_news(d.year, d.month))
            else:
                st.error("❌ 오답. 이번 달 뉴스는 공개되지 않습니다.")
    else:
        st.info("퀴즈가 모두 소진되었습니다.")

    st.markdown("---")

    # ── 팀 탭 ─────────────────────────────────────────────
    tabs = st.tabs([t.name for t in game.teams])
    for i, team in enumerate(game.teams):
        with tabs[i]:
            if team.is_bankrupt:
                st.error("💀 파산 — 자산이 초기 자본의 10% 미만입니다.")
                continue

            total = team.get_total_value_krw(game.get_price, game.current_date)
            st.metric("총 자산 (원화 환산)", f"{total:,.0f} 원")
            ca, cb = st.columns(2)
            ca.metric("보유 원화", f"{team.krw_balance:,.0f} 원")
            cb.metric("보유 달러", f"$ {team.usd_balance:,.2f}")

            st.markdown("##### 포트폴리오")
            show_portfolio(team, game.get_price, game.current_date)
            st.markdown("---")

            col_trade, col_fx = st.columns(2)

            # ── 주식 거래 ──
            with col_trade:
                st.write("**📈 주식 거래**")
                ticker = st.selectbox(
                    "종목 선택",
                    game.tradeable_tickers,
                    format_func=ticker_label,
                    key=f"tk_{safe_key(team.name)}",
                )
                price_now = game.get_price(ticker, game.current_date)
                is_kr = ticker.endswith('.KS')
                bal = team.krw_balance if is_kr else team.usd_balance
                max_buy = max(1, int(bal / price_now)) if price_now > 0 else 1

                qty = quantity_input(
                    f"수량 (최대 {max_buy:,}주)",
                    key=f"qty_{safe_key(team.name)}_{safe_key(ticker)}_{game.current_turn}",
                    max_val=max_buy,
                )

                if price_now > 0:
                    est = price_now * qty
                    st.caption(f"예상 금액: {'%s원' % f'{est:,.0f}' if is_kr else '$%s' % f'{est:,.2f}'}")

                btn1, btn2 = st.columns(2)
                if btn1.button("매수", key=f"buy_{safe_key(team.name)}"):
                    ok, msg = game.buy_stock(team, ticker, qty)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                if btn2.button("매도", key=f"sell_{safe_key(team.name)}"):
                    ok, msg = game.sell_stock(team, ticker, qty)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

            # ── 환전 ──
            with col_fx:
                st.write("**💱 환전**")
                show_fx_box(game.get_price('USDKRW=X', game.current_date))
                fx_amt = st.number_input(
                    "환전 금액 (달러 기준)",
                    min_value=100.0, step=100.0,
                    key=f"fx_{safe_key(team.name)}",
                )
                f1, f2 = st.columns(2)
                if f1.button("달러 매수 →", key=f"buyfx_{safe_key(team.name)}"):
                    ok, msg = game.exchange_currency(team, 'KRW_TO_USD', fx_amt)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                if f2.button("← 달러 매도", key=f"sellfx_{safe_key(team.name)}"):
                    ok, msg = game.exchange_currency(team, 'USD_TO_KRW', fx_amt)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    # ── 다음 턴 ──
    st.markdown("---")
    if st.button("⏭️ 다음 턴 (1개월 후)"):
        game.next_turn()
        st.session_state.quiz_answered = False
        st.session_state.news_unlocked = False
        st.session_state.current_quiz = game.quizzes.pop() if game.quizzes else None
        if game.current_turn > game.total_turns:
            st.session_state.game_over = True
        st.rerun()


if __name__ == "__main__":
    main()
