# NOTE: This app requires Streamlit to be installed. Run `pip install streamlit` before executing.

try:
    import streamlit as st
except ModuleNotFoundError:
    print("Streamlit is not installed. Please install it using 'pip install streamlit'.")
    st = None

import uuid
import datetime
import random

# Simulated database using session_state
if st:
    if "sessions" not in st.session_state:
        st.session_state["sessions"] = {}
    sessions = st.session_state["sessions"]

    # Default page title
    page_title = "What Time Will [Name] Get Here?"

    # Update page title if target name is known
    if "last_session_id" in st.session_state:
        last_id = st.session_state["last_session_id"]
        if last_id in sessions and sessions[last_id].get("target_name"):
            page_title = f"What Time Will {sessions[last_id]['target_name']} Get Here?"

    st.set_page_config(page_title=page_title, layout="centered")
    st.title(f"📍 {page_title}")

    if "show_session_created" in st.session_state:
        st.success(f"✅ New session created! Session Code: **{st.session_state['show_session_created']}**")
        del st.session_state["show_session_created"]

    # --- Game Host or Join or View ---
    timezone = st.selectbox("Select your timezone:", ["UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific"], index=1)
    import pytz
    user_tz = pytz.timezone(timezone)

    mode = st.radio("Select a mode:", ["Host", "Join", "Active Game"])

    if mode == "Host":
        st.subheader("🎉 Host a New Game")
        interval = st.selectbox("Pick a time interval for guesses:", [5, 10, 15, 20, 30])
        target_name = st.text_input("Who are you waiting for? (Name)")
        test_mode = st.checkbox("Enable test mode with fake players")

        if st.button("Start Game") and target_name:
            session_id = str(uuid.uuid4())[:6]
            now = datetime.datetime.now(pytz.utc).astimezone(user_tz)
            next_minute = ((now.minute // interval) + 1) * interval
            if next_minute >= 60:
                start_time = (now + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            else:
                start_time = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(minutes=next_minute)

            end_of_day = datetime.datetime.combine(start_time.date(), datetime.time(23, 59), tzinfo=start_time.tzinfo)
            block_count = int(((end_of_day - start_time).seconds) / (interval * 60))
            blocks = [start_time + datetime.timedelta(minutes=i * interval) for i in range(block_count)]
            block_labels = [f"{b.strftime('%I:%M %p')} - {(b + datetime.timedelta(minutes=interval)).strftime('%I:%M %p')}" for b in blocks] + ["They never show up"]

            sessions[session_id] = {
                "interval": interval,
                "target_name": target_name,
                "start_time": start_time,
                "players": {},
                "arrival_time": None,
                "block_labels": block_labels,
                "blocks": blocks
            }

            if test_mode:
                fake_users = ["Alice", "Bob", "Charlie", "Daisy", "Eli"]
                for user in fake_users:
                    available_blocks = [label for label in block_labels if label not in sessions[session_id]["players"].values()]
                    if available_blocks:
                        choice = random.choice(available_blocks)
                        sessions[session_id]["players"][user] = choice

            st.session_state["last_session_id"] = session_id
            st.session_state["show_session_created"] = session_id
            st.rerun()  # Refresh to update the page title with the entered name
            st.rerun()  # Refresh to update the page title with the entered name

    if mode in ["Join", "Active Game"]:
        st.subheader("🔎 Session Info")
        session_id = st.text_input("Enter session code:", st.session_state.get("last_session_id", ""))

        if not session_id:
            st.warning("Please enter a session code to continue.")

        elif session_id not in sessions:
            st.error("That session code was not found. Please check and try again.")

        else:
            game = sessions[session_id]
            interval = game["interval"]
            start_time = game["start_time"]
            blocks = game["blocks"]
            block_labels = game["block_labels"]
            now = datetime.datetime.now(datetime.timezone.utc).astimezone()

            if mode == "Join":
                st.subheader("👋 Join the Game")
                username = st.text_input("Pick a username:")
                joined = st.button("Join Game")

                if username and joined:
                    st.session_state["current_username"] = username

                current_user = st.session_state.get("current_username")

                if current_user:
                    taken_blocks = list(game["players"].values())
                    available_blocks = [label for label in block_labels if label not in taken_blocks]

                    if not available_blocks:
                        st.warning("No available time blocks left to choose from.")
                    else:
                        block_choice = st.radio("Pick your time block:", available_blocks, key="time_block")

                        if st.button("Lock In My Guess"):
                            if current_user not in game["players"]:
                                game["players"][current_user] = block_choice
                                st.success("Guess locked in!")
                            else:
                                st.warning("You've already picked a block!")

                if game["players"]:
                    st.markdown("---")
                    st.subheader("Current Picks")
                    sorted_players = sorted(game["players"].items(), key=lambda x: block_labels.index(x[1]) if x[1] in block_labels else float('inf'))
                    for user, choice in sorted_players:
                        st.write(f"**{user}** picked: {choice}")

                button_label = f"📍 {game['target_name']} Arrived!" if game.get('target_name') else "📍 They Arrived!"
                if st.button(button_label):
                    game["arrival_time"] = datetime.datetime.now(pytz.utc).astimezone(user_tz)
                    arrival_time = game["arrival_time"]
                    st.success(f"{game['target_name']} arrived at {arrival_time.strftime('%I:%M %p')}!")

                    winner_found = False
                    for i, b in enumerate(blocks):
                        block_end = b + datetime.timedelta(minutes=interval)
                        if b <= arrival_time < block_end:
                            winning_block = block_labels[i]
                            winners = [user for user, choice in game["players"].items() if choice == winning_block]
                            if winners:
                                winner_found = True
                                for winner in winners:
                                    st.balloons()
                                    st.success(f"🎉 Winner: {winner} with the time block {winning_block}!")
                            else:
                                st.info(f"Arrival was in the block {winning_block}, but no one picked it.")
                            break

                    if not winner_found:
                        st.info("No winning guess. Either the block wasn't picked or arrival didn't match any window.")

            if mode == "Active Game":
                st.subheader("📊 Game Leaderboard")
                st.write(f"Tracking **{game['target_name']}** | Interval: {interval} minutes")
                st.write(f"Start Time: {start_time.strftime('%I:%M %p')} | Session Code: **{session_id}**")

                st.subheader("Leaderboard & Status")
                st.caption(f"Current Time: {now.strftime('%I:%M %p %Z')}")
                arrival_time = game["arrival_time"]
                players = game["players"]

                sorted_blocks = [(i, block_labels[i]) for i in range(len(block_labels))]

                for i, label in sorted_blocks:
                    block_start = blocks[i] if i < len(blocks) else None
                    block_end = block_start + datetime.timedelta(minutes=interval) if block_start else None
                    status = "🟡 Upcoming"

                    if arrival_time and block_start and block_end:
                        if block_start <= arrival_time < block_end:
                            status = "✅ Winning Block"
                        elif arrival_time >= block_end:
                            status = "⚫ Passed"
                    elif block_start and block_end:
                        if now >= block_end:
                            status = "⚫ Passed"
                        elif now >= block_start:
                            status = "🔵 Current"

                    claimed_by = [name for name, pick in players.items() if pick == label]
                    pick_status = f"{label} — {status}"
                    if claimed_by:
                        pick_status += f" — Claimed by: {', '.join(claimed_by)}"
                    else:
                        pick_status += " — ⏳ Unclaimed"
                    st.write(pick_status)

else:
    print("App not running in Streamlit environment.")
