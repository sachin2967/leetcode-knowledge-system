"""Thin local Streamlit client; every domain operation goes through FastAPI."""

import os

import httpx
import streamlit as st

API_URL = os.environ.get("LKS_API_URL", "http://127.0.0.1:8000").rstrip("/")


def api(method: str, path: str, payload: dict | None = None):
    try:
        response = httpx.request(
            method, API_URL + path, json=payload, timeout=30, trust_env=False
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        st.error(
            f"API request failed ({exc.response.status_code}): {exc.response.text}"
        )
    except httpx.RequestError:
        st.error("API unavailable. Start the local FastAPI server and retry.")
    return None


def main() -> None:
    st.set_page_config(page_title="Knowledge-aware practice", layout="wide")
    st.title("Knowledge-aware LeetCode practice")
    st.caption("Ready means defined prerequisite coverage, never solve probability.")
    st.info(
        "Public mode uses up to 20 recent accepted submissions, not full history. "
        "Unmapped problems and incomplete evidence remain visible below."
    )
    catalog = api("GET", "/catalog")
    concepts = api("GET", "/concepts")
    if catalog is None or concepts is None:
        return
    with st.form("practice"):
        mode = st.radio("Profile source", ["demo", "public"], horizontal=True)
        username = st.text_input("Public username (public mode only)")
        query = st.text_input("Practice query", value="sliding window")
        requested = st.multiselect("Concepts", concepts)
        difficulty = st.selectbox(
            "Preferred difficulty", ["Any", "Easy", "Medium", "Hard"]
        )
        targets = {p["problem_id"]: f"{p['problem_id']}: {p['title']}" for p in catalog}
        target = st.selectbox(
            "Target to diagnose",
            [None, *targets],
            format_func=lambda value: targets.get(value, "No target"),
        )
        submitted = st.form_submit_button("Build profile and practice plan")
    if submitted:
        source = {"mode": mode}
        if mode == "public":
            source["username"] = username
        result = api(
            "POST",
            "/practice",
            {
                "source": source,
                "query": query,
                "concepts": requested,
                "difficulty": None if difficulty == "Any" else difficulty,
                "target_problem_id": target,
            },
        )
        # Clear previous results on failure so another user's old profile is not shown.
        st.session_state["practice_result"] = result
    result = st.session_state.get("practice_result")
    if result:
        profile = result["profile"]
        st.subheader(f"Concept evidence: {profile['username']}")
        st.write(
            f"{profile['mapped_solves']} mapped solves / {profile['reported_solves']} reported. "
            f"Source: {profile['source']}; collected {profile['collected_at']}."
        )
        for note in profile["uncertainty"]:
            st.warning(note)
        st.dataframe(profile["concepts"], hide_index=True)
        with st.expander("Full profile and unmapped identifiers"):
            st.json(profile)
        st.subheader("Query recommendations")
        if result["recommendations"]:
            st.dataframe(result["recommendations"], hide_index=True)
        else:
            st.info(
                "No query recommendations. Try a title, topic, or explicit concept."
            )
        diagnosis = result["diagnosis"]
        if diagnosis:
            st.subheader(f"{diagnosis['target_title']}: {diagnosis['readiness']}")
            st.write(diagnosis["explanation"])
            st.dataframe(diagnosis["concepts"], hide_index=True)
            st.write("Gap practice path (Easy to Hard)")
            if diagnosis["practice_path"]:
                st.dataframe(diagnosis["practice_path"], hide_index=True)
            else:
                st.info(
                    "No gap practice is required by the defined coverage threshold."
                )
            with st.form("socratic_mentor"):
                question = st.text_input(
                    "What part are you stuck on?", value="How should I start?"
                )
                level = st.select_slider(
                    "Hint level",
                    options=[1, 2, 3, 4],
                    value=1,
                    format_func=lambda value: {
                        1: "1 · Intuition",
                        2: "2 · Data structure",
                        3: "3 · Invariant",
                        4: "4 · Edge cases",
                    }[value],
                )
                mentor_submit = st.form_submit_button("Get a Socratic hint")
            if mentor_submit:
                hint = api(
                    "POST",
                    "/mentor",
                    {
                        "problem_id": diagnosis["target_problem_id"],
                        "question": question,
                        "level": level,
                    },
                )
                if hint:
                    st.info(f"{hint['level_name']}: {hint['hint']}")
                    st.caption(
                        "Retrieved evidence: " + " · ".join(hint["retrieved_evidence"])
                    )
                    st.caption(hint["safety"])

    with st.expander("My accepted code — local owner-authorized access"):
        st.caption(
            "Local trusted use only; owner names are not authentication. "
            "Imports replace that owner's corpus. No code is fetched from LeetCode."
        )
        with st.form("personal"):
            owner = st.text_input("Corpus owner")
            authorized = st.checkbox(
                "I own this corpus and authorize local import/retrieval"
            )
            source_path = st.text_input("Import JSON path relative to data/raw")
            template_query = st.text_input("Template search", value="arrays_hashing")
            do_import = st.form_submit_button("Import accepted code")
            do_search = st.form_submit_button("Find my templates")
        if do_import or do_search:
            payload = {"owner": owner, "owner_authorized": authorized}
            if do_import:
                imported = api(
                    "POST", "/personal/import", {**payload, "source": source_path}
                )
                if imported is not None:
                    st.success(f"Imported {imported['imported']} accepted snippets.")
            else:
                found = api(
                    "POST", "/personal/templates", {**payload, "query": template_query}
                )
                if found is not None:
                    st.write(f"Corpus search: {found['status']}")
                    for snippet in found["snippets"]:
                        st.write(
                            f"{snippet['owner']} · {snippet['problem_id']}: {snippet['title']} · {snippet['language']}"
                        )
                        st.code(snippet["code"])


if __name__ == "__main__":
    main()
