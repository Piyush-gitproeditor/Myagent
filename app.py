import subprocess
import sys
import streamlit as st
from chat_agent import chat_turn, write_pack, PROFILE
from config import BASE_DIR

st.set_page_config(page_title="Opportunity Agent", page_icon="🎯")
st.title("🎯 Opportunity Agent")
st.caption("Tell me what you're looking for: hackathons, internships, jobs.")

ss = st.session_state
ss.setdefault("history", [])   # {"role", "content", "cards"}
ss.setdefault("status", {})    # url -> "applying" | "applied" | "skipped"
ss.setdefault("proc", None)
ss.setdefault("packs", {})     # url -> generated pack text

def open_form(url):
    if ss.proc and ss.proc.poll() is None:
        st.warning("A browser window is already open. Finish and close it first.")
        return False
    ss.proc = subprocess.Popen(
        [sys.executable, str(BASE_DIR / "apply_helper.py"), url], cwd=str(BASE_DIR))
    return True


def contact_block():
    fields = [("name", "Name"), ("email", "Email"), ("phone", "Phone"), ("college", "College"),
              ("city", "City"), ("github", "GitHub"), ("linkedin", "LinkedIn")]
    return "\n".join(f"{label}: {PROFILE[k]}" for k, label in fields if PROFILE.get(k))


def render_card(card, key):
    url = card.get("url", "")
    state = ss.status.get(url)
    with st.container(border=True):
        title = f"**{card.get('title', 'Untitled')}**"
        if card.get("company"):
            title += f" — {card['company']}"
        st.markdown(title)
        meta = " · ".join(x for x in (card.get("kind"),
                          f"⏰ {card['deadline']}" if card.get("deadline") else None) if x)
        if meta:
            st.caption(meta)
        if card.get("details"):
            st.write(card["details"])

        if state == "applied":
            st.success("Marked as applied ✅")
        elif state == "skipped":
            st.caption("Skipped")
        elif state == "applying":
            st.info("Browser is open. Solve any CAPTCHA/OTP, review and submit, then close that window.")
            if st.button("✔ I submitted it", key=f"done-{key}"):
                ss.status[url] = "applied"
                st.rerun()
        else:
            c1, c2, c3 = st.columns(3)
            c1.link_button("Open page", url)
            if c2.button("🖥 Open in agent browser", key=f"apply-{key}"):
                if open_form(url):
                    ss.status[url] = "applying"
                    st.rerun()
            if c3.button("⏭ Skip", key=f"skip-{key}"):
                ss.status[url] = "skipped"
                st.rerun()

        # Application pack (available unless skipped)
        if state != "skipped":
            if url in ss.packs:
                with st.expander("📝 Application pack", expanded=True):
                    st.markdown(ss.packs[url])
                    block = contact_block()
                    if block:
                        st.caption("Your details (use the copy icon):")
                        st.code(block, language=None)
                    st.caption("Review and edit before using. Check every claim is true.")
            elif st.button("📝 Application pack", key=f"pack-{key}"):
                with st.spinner("Writing..."):
                    try:
                        ss.packs[url] = write_pack(card)
                    except Exception as e:
                        ss.packs[url] = f"Something went wrong: {e}"
                st.rerun()

for i, m in enumerate(ss.history):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        for j, card in enumerate(m.get("cards", [])):
            render_card(card, f"{i}-{j}")

if prompt := st.chat_input("e.g. find me data science internships and open hackathons"):
    ss.history.append({"role": "user", "content": prompt})

    # what the model sees: plain text, plus a note of which cards it already showed
    model_history = []
    for m in ss.history:
        text = m["content"]
        if m.get("cards"):
            text += "\n(Cards shown: " + "; ".join(c.get("title", "") for c in m["cards"]) + ")"
        model_history.append({"role": m["role"], "content": text})

    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Searching..."):
            try:
                reply, cards = chat_turn(model_history)
            except Exception as e:
                reply, cards = f"Something went wrong: {e}", []
    ss.history.append({"role": "assistant", "content": reply, "cards": cards})
    st.rerun()