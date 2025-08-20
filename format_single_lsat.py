import re

def format_first_lsat_question():
    """첫 번째 LSAT 문제만 수동으로 포맷팅합니다"""
    
    # 첫 번째 문제의 원본 내용 (라인 13-51 기준)
    problem_text = """CEO: While we only have the sales reports for the
first 9 months of this year, I feel confident in
concluding that this will be a good year for us
in terms of sales. In each of the last 5 years, our
monthly sales average was less than $30 million.
However, our monthly sales average so far for
this year is over $35 million.
Which one of the following, if true, most strengthens the
CEO's argument?"""

    # 보기 텍스트들 (순서대로)
    choices = [
        "The CEO's company typically has its highest monthly sales of the year during the last 3 months of the year.",
        "The quality of the products sold by the CEO's company has always been considered to be relatively high.",
        "The CEO has a strong incentive to highlight any good news regarding the company and to downplay bad news.",
        "The CEO'scompany started a new advertising campaign at the beginning of this year that has proved unusually effective so far.",
        "Several other companies who sell products similar to those sold by the CEO's company have also reported that this year's monthly sales averages so far have been higher than previous years' averages."
    ]
    
    # 포맷팅된 문제 생성
    formatted = "1.\n"
    formatted += problem_text + "\n"
    
    # 보기 추가
    letters = ['A', 'B', 'C', 'D', 'E']
    for i, choice in enumerate(choices):
        formatted += f"\n({letters[i]}) {choice}"
    
    return formatted

def format_second_lsat_question():
    """두 번째 LSAT 문제만 수동으로 포맷팅합니다"""
    
    problem_text = """Javier: Government workers are paid higher hourly
wages than comparable private sector employees.
So the government could save money by hiring
private contractors to perform services now
performed by government employees.
Mykayla: An analysis of government contracts
showed that, on average, the government paid
substantially more to hire contractors than it
would have cost for government employees to
perform comparable services.
Javier and Mykayla disagree with each other over
whether"""

    choices = [
        "the government could reduce spending by reducing the number of employees on its payroll",
        "the government would save money if it hired private contractors to perform services now performed by government employees",
        "government workers generally are paid higher hourly wages than comparable private sector workers", 
        "every service that is currently performed by government employees could be performed by private contractors",
        "the total amount of money that the government pays its employees annually is greater than the total amount that it spends on contractors annually"
    ]
    
    formatted = "2.\n"
    formatted += problem_text + "\n"
    
    letters = ['A', 'B', 'C', 'D', 'E']
    for i, choice in enumerate(choices):
        formatted += f"\n({letters[i]}) {choice}"
    
    return formatted

def main():
    print("=" * 60)
    print("LSAT 문제 수동 포맷팅 (처음 2문제)")
    print("=" * 60)
    
    # 첫 번째 문제 포맷팅
    problem1 = format_first_lsat_question()
    print("첫 번째 문제:")
    print(problem1)
    print("\n" + "="*60 + "\n")
    
    # 두 번째 문제 포맷팅
    problem2 = format_second_lsat_question()
    print("두 번째 문제:")
    print(problem2)
    
    # 파일에 저장할지 물어보기
    print("\n" + "="*60)
    print("이 내용을 LSAT_formatted_sample.txt 파일로 저장하시겠습니까? (y/N): ", end="")
    
    # 자동으로 저장
    print("y")
    
    formatted_content = problem1 + "\n\n" + problem2
    
    try:
        with open('questionbank/lsat/LSAT_formatted_sample.txt', 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        print("✅ LSAT_formatted_sample.txt 파일로 저장되었습니다!")
        print("이 형식을 참고하여 나머지 문제들도 수동으로 수정하세요.")
    except Exception as e:
        print(f"❌ 파일 저장 오류: {e}")

if __name__ == "__main__":
    main() 