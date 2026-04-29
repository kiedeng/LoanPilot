from datetime import date, timedelta

from app.db.session import SessionLocal
from app.models.domain import LoanAccount, LoanProduct, RepaymentPlan, User


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        for user in [
            User(id=1, name="Demo Personal", segment="personal"),
            User(id=2, name="Demo Business", segment="business"),
            User(id=3, name="Demo Existing", segment="existing"),
            User(id=4, name="Demo Wealth", segment="wealth"),
        ]:
            db.merge(user)

        for product in [
            LoanProduct(
                id="consumer_loan",
                name="个人消费贷",
                segment="personal",
                max_amount=300000,
                rate_range="3.8%-7.2%",
                term_range="12-60个月",
                disbursement="最快1个工作日",
                description="适合装修、教育、旅行等合法消费用途。",
            ),
            LoanProduct(
                id="business_loan",
                name="小微经营贷",
                segment="business",
                max_amount=1000000,
                rate_range="4.0%-8.5%",
                term_range="6-36个月",
                disbursement="2-3个工作日",
                description="适合小微企业主经营周转、采购备货等用途。",
            ),
            LoanProduct(
                id="wealth_liquidity_loan",
                name="理财客户流动性贷",
                segment="wealth",
                max_amount=500000,
                rate_range="3.6%-6.8%",
                term_range="3-36个月",
                disbursement="最快当天",
                description="适合银行理财客户短期流动性需求。",
            ),
        ]:
            db.merge(product)

        if db.query(LoanAccount).count() == 0:
            account = LoanAccount(
                id="LN-DEMO-001",
                user_id=3,
                product_name="个人消费贷",
                principal=200000,
                outstanding_balance=126000,
                next_due_amount=4360.22,
                next_due_date=(date.today() + timedelta(days=12)).isoformat(),
            )
            db.add(account)
            for period in range(1, 7):
                db.add(
                    RepaymentPlan(
                        loan_account_id=account.id,
                        period=period,
                        due_date=(date.today() + timedelta(days=30 * period)).isoformat(),
                        amount=4360.22,
                        principal=3980.12,
                        interest=380.10,
                        status="pending",
                    )
                )
        db.commit()
    finally:
        db.close()
