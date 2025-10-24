from __future__ import annotations

import argparse

from sqlalchemy import select

from .db import session_scope
from .modules.users.models import User, Group, INITIAL_GROUPS


def seed_groups() -> int:
    with session_scope() as sess:
        existing = {g.name for g in sess.scalars(select(Group)).all()}
        created = 0
        for name in INITIAL_GROUPS:
            if name not in existing:
                sess.add(Group(name=name, description=name))
                created += 1
        print(f"Created {created} groups; {len(existing)} already existed.")
    return 0


def create_user(email: str, display_name: str, password: str) -> int:
    with session_scope() as sess:
        if sess.scalar(select(User).where(User.email == email)):
            print("User already exists:", email)
            return 1
        u = User(email=email, display_name=display_name, password_hash="")
        u.set_password(password)
        sess.add(u)
        print("Created user:", email)
    return 0


def add_group(email: str, group_name: str) -> int:
    with session_scope() as sess:
        user = sess.scalar(select(User).where(User.email == email))
        if not user:
            print("No such user:", email)
            return 1
        grp = sess.scalar(select(Group).where(Group.name == group_name))
        if not grp:
            grp = Group(name=group_name, description=group_name)
            sess.add(grp)
            sess.flush()
        if grp not in user.groups:
            user.groups.append(grp)
        print(f"Added group '{group_name}' to {email}")
    return 0


def promote_admin(email: str) -> int:
    for g in ("user", "admin"):
        rc = add_group(email, g)
        if rc != 0:
            return rc
    print("Promoted to admin:", email)
    return 0


def create_admin(email: str, display_name: str, password: str) -> int:
    with session_scope() as sess:
        user = sess.scalar(select(User).where(User.email == email))
        if not user:
            user = User(email=email, display_name=display_name, password_hash="")
            user.set_password(password)
            sess.add(user)
            sess.flush()
            print("Created user:", email)
        else:
            # Update display_name/password if provided
            user.display_name = display_name or user.display_name
            if password:
                user.set_password(password)
            print("Updated user (if needed):", email)
        # ensure groups
        grp_user = sess.scalar(select(Group).where(Group.name == "user")) or Group(name="user", description="user")
        grp_admin = sess.scalar(select(Group).where(Group.name == "admin")) or Group(name="admin", description="admin")
        if grp_user not in user.groups:
            user.groups.append(grp_user)
        if grp_admin not in user.groups:
            user.groups.append(grp_admin)
        print("Granted admin privileges to:", email)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kfamily-cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("seed-groups")

    p_create = sub.add_parser("create-user")
    p_create.add_argument("email")
    p_create.add_argument("display_name")
    p_create.add_argument("password")

    p_addg = sub.add_parser("add-group")
    p_addg.add_argument("email")
    p_addg.add_argument("group")

    p_promote = sub.add_parser("promote-admin")
    p_promote.add_argument("email")

    p_create_admin = sub.add_parser("create-admin")
    p_create_admin.add_argument("email")
    p_create_admin.add_argument("display_name")
    p_create_admin.add_argument("password")

    args = parser.parse_args(argv)

    if args.cmd == "seed-groups":
        return seed_groups()
    if args.cmd == "create-user":
        return create_user(args.email, args.display_name, args.password)
    if args.cmd == "add-group":
        return add_group(args.email, args.group)
    if args.cmd == "promote-admin":
        return promote_admin(args.email)
    if args.cmd == "create-admin":
        return create_admin(args.email, args.display_name, args.password)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
