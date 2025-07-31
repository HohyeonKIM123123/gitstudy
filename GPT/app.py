import streamlit as st
import pandas as pd
from email_client.imap_service import fetch_emails
from email_client.smtp_service import send_email
from ai.classifier import classify_email
from ai.reply_generator import generate_reply
from db.database import init_db
from db.email_repository import save_received_email, save_sent_email, get_received_emails, get_sent_emails

# DB 초기화
init_db()

st.set_page_config(page_title="📧 이메일 자동 회신 비서", layout="wide")
st.title("📧 이메일 자동 회신 비서")

# 사이드바 설정
st.sidebar.header("⚙️ 설정")
st.session_state.simplify_mode = st.sidebar.toggle("간결화 모드", value=False)

tab1, tab2, tab3 = st.tabs(["📥 받은 이메일", "📤 보낸 이메일", "📊 이메일 기록"])

with tab1:
    if "emails" not in st.session_state:
        st.session_state.emails = fetch_emails()

    if st.button("이메일 새로고침"):
        st.session_state.emails = fetch_emails()

    emails = st.session_state.emails

    if emails:
        df = pd.DataFrame(emails)
        st.dataframe(df[["from", "subject"]])

        selected_idx = st.number_input("확인할 이메일 번호", min_value=0, max_value=len(emails)-1, value=0)
        email_data = emails[selected_idx]

        st.subheader(f"제목: {email_data['subject']}")
        st.write(f"보낸 사람: {email_data['from']}")
        st.text_area("본문", email_data["body"], height=200)

        classification = classify_email(email_data["subject"], email_data["body"])
        st.write(f"📌 분류: {classification}")

        # DB 저장 (중복 방지)
        if st.button("이메일 기록 저장"):
            save_received_email(email_data["from"], email_data["subject"], email_data["body"], classification)
            st.success("이메일 기록이 저장되었습니다!")

        if st.button("GPT 회신 초안 생성"):
            draft = generate_reply(email_data["body"], classification)
            st.session_state.draft = draft

        if "draft" in st.session_state:
            reply_body = st.text_area("회신 초안", st.session_state.draft, height=150)
            recipient = st.text_input("받는 사람", value=email_data["from"])

            if st.button("이메일 발송"):
                if send_email(recipient, f"Re: {email_data['subject']}", reply_body):
                    save_sent_email(recipient, f"Re: {email_data['subject']}", reply_body)
                    st.success("이메일 발송 성공!")
                else:
                    st.error("이메일 발송 실패")
    else:
        st.warning("이메일을 불러올 수 없습니다.")

with tab2:
    st.subheader("보낸 이메일 기록")
    sent_records = get_sent_emails()
    if sent_records:
        st.dataframe(pd.DataFrame(sent_records, columns=["받는 사람", "제목", "보낸 시간"]))
    else:
        st.info("보낸 이메일 기록이 없습니다.")

with tab3:
    st.subheader("받은 이메일 기록")
    received_records = get_received_emails()
    if received_records:
        st.dataframe(pd.DataFrame(received_records, columns=["보낸 사람", "제목", "분류", "받은 시간"]))
    else:
        st.info("받은 이메일 기록이 없습니다.")
