from __future__ import annotations


def render_rejection_email(candidate_name: str, role_title: str) -> tuple[str, str, str]:
    name = candidate_name.strip() or "there"
    role = role_title.strip() or "the role"
    subject = f"Update on your application for {role}"
    text = (
        f"Hi {name},\n\n"
        f"Thank you for taking the time to apply for {role} and for sharing your background with us. "
        f"After careful review, we've decided to move forward with other candidates whose experience "
        f"more closely matches what we need for this position right now.\n\n"
        f"We were genuinely glad to learn about your work, and we'd encourage you to apply again for "
        f"future openings that fit your skills.\n\n"
        f"Wishing you the very best in your search.\n\n"
        f"Best regards,\nHiring Team"
    )
    html = (
        f"<p>Hi {name},</p>"
        f"<p>Thank you for taking the time to apply for <strong>{role}</strong> and for sharing your "
        f"background with us. After careful review, we've decided to move forward with other candidates "
        f"whose experience more closely matches what we need for this position right now.</p>"
        f"<p>We were genuinely glad to learn about your work, and we'd encourage you to apply again for "
        f"future openings that fit your skills.</p>"
        f"<p>Wishing you the very best in your search.</p>"
        f"<p>Best regards,<br/>Hiring Team</p>"
    )
    return subject, html, text


def render_interview_invite_email(
    candidate_name: str, role_title: str, round_label: str, slots: list[str]
) -> tuple[str, str, str]:
    name = candidate_name.strip() or "there"
    role = role_title.strip() or "the role"
    round_name = round_label.strip() or "an interview"
    subject = f"You're invited to {round_name} for {role}"
    slot_lines = "\n".join(f"- {slot}" for slot in slots) if slots else "- We'll follow up with timing shortly."
    slot_items = "".join(f"<li>{slot}</li>" for slot in slots) if slots else "<li>We'll follow up with timing shortly.</li>"
    text = (
        f"Hi {name},\n\n"
        f"Great news — we'd like to invite you to {round_name} for {role}. Here are some proposed times:\n\n"
        f"{slot_lines}\n\n"
        f"Reply and let us know what works best for you.\n\n"
        f"Best regards,\nHiring Team"
    )
    html = (
        f"<p>Hi {name},</p>"
        f"<p>Great news — we'd like to invite you to <strong>{round_name}</strong> for <strong>{role}</strong>. "
        f"Here are some proposed times:</p>"
        f"<ul>{slot_items}</ul>"
        f"<p>Reply and let us know what works best for you.</p>"
        f"<p>Best regards,<br/>Hiring Team</p>"
    )
    return subject, html, text


def render_offer_email(candidate_name: str, role_title: str) -> tuple[str, str, str]:
    name = candidate_name.strip() or "there"
    role = role_title.strip() or "the role"
    subject = f"An offer for {role}"
    text = (
        f"Hi {name},\n\n"
        f"Congratulations! We're excited to offer you the {role} position. We were impressed by your "
        f"experience throughout the process and think you'd be a great fit for the team.\n\n"
        f"We'll follow up shortly with the full offer details. Congratulations again!\n\n"
        f"Best regards,\nHiring Team"
    )
    html = (
        f"<p>Hi {name},</p>"
        f"<p>Congratulations! We're excited to offer you the <strong>{role}</strong> position. We were "
        f"impressed by your experience throughout the process and think you'd be a great fit for the team.</p>"
        f"<p>We'll follow up shortly with the full offer details. Congratulations again!</p>"
        f"<p>Best regards,<br/>Hiring Team</p>"
    )
    return subject, html, text
