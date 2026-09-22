#!/usr/bin/env python3
"""
그룹과제 팀 편성 프로그램

- 수강생 39명 + 청강생 2명 = 총 41명
- 학생 이름을 한 줄에 4~5명씩 입력받아, 한 줄(묶음)씩 A, B, C, D팀에 랜덤 배치
  - 4명 묶음: 네 팀에 한 명씩
  - 5명 묶음: 네 팀에 한 명씩 + 한 팀에 한 명 더
  -> 결과(41명): 10명 팀 3개 + 11명 팀 1개
- 특정 학생을 원하는 팀에 고정 배치 가능 (예: 김제민=A)

사용법:
    python team_assign.py                 # 4명씩 직접 입력
    python team_assign.py names.txt       # 파일에서 이름 읽기 (한 줄에 4~5명, 쉼표 구분)
    python team_assign.py names.txt --seed 42   # 결과 재현용 시드 지정
    python team_assign.py names.txt --fix 김제민=A --fix 홍길동=C   # 특정 학생 팀 고정
"""

import argparse
import random
import sys

TEAMS = ["A", "B", "C", "D"]
TOTAL_STUDENTS = 41
MIN_GROUP, MAX_GROUP = 4, 5  # 한 번에 입력/배치하는 인원


def parse_names(text):
    """쉼표 또는 줄바꿈으로 구분된 이름 목록을 리스트로 변환한다."""
    return [n for g in parse_groups(text) for n in g]


def parse_groups(text):
    """한 줄을 하나의 묶음으로 보고, 쉼표로 구분된 이름을 읽는다."""
    groups = []
    for line in text.splitlines():
        group = [n.strip() for n in line.split(",") if n.strip()]
        if group:
            groups.append(group)
    return groups


def normalize_groups(groups):
    """
    묶음 크기를 확인한다. 한 줄에 한 명씩 적힌 파일이면 4명씩 묶는다.
    각 묶음은 4~5명이어야 하며, 마지막 묶음만 4명보다 적어도 된다.
    """
    if groups and all(len(g) == 1 for g in groups):
        names = [g[0] for g in groups]
        groups = [names[i:i + MIN_GROUP] for i in range(0, len(names), MIN_GROUP)]
    for i, g in enumerate(groups):
        last = i == len(groups) - 1
        if len(g) > MAX_GROUP or (len(g) < MIN_GROUP and not last):
            raise ValueError(f"{i + 1}번째 줄은 {len(g)}명입니다. 한 줄에는 {MIN_GROUP}~{MAX_GROUP}명을 입력하세요.")
    return groups


def input_groups_interactively(total=TOTAL_STUDENTS):
    """학생 이름을 한 번에 4~5명씩 입력받는다."""
    groups, names = [], []
    print(f"학생 {total}명의 이름을 한 번에 {MIN_GROUP}~{MAX_GROUP}명씩 쉼표(,)로 구분하여 입력하세요.")
    while len(names) < total:
        left = total - len(names)
        lo, hi = min(MIN_GROUP, left), min(MAX_GROUP, left)
        need = f"{lo}명" if lo == hi else f"{lo}~{hi}명"
        line = input(f"[{len(groups) + 1}번째 입력] {need} ({len(names)}/{total}): ")
        batch = parse_names(line)
        if not lo <= len(batch) <= hi:
            print(f"  -> {need}을 입력해야 합니다. (입력된 인원: {len(batch)}명) 다시 입력하세요.")
            continue
        duplicated = [n for n in batch if n in names or batch.count(n) > 1]
        if duplicated:
            print(f"  -> 중복된 이름이 있습니다: {', '.join(sorted(set(duplicated)))}. 다시 입력하세요.")
            continue
        groups.append(batch)
        names.extend(batch)
    return groups


def team_capacities(total, fixed, rng=random):
    """
    팀별 정원을 정한다. 기본 정원은 total // 4명이고, 나머지 인원만큼
    랜덤한 팀의 정원이 1명씩 늘어난다. (41명 -> 10, 10, 10, 11)
    고정 배치 인원이 기본 정원보다 많은 팀은 반드시 정원이 늘어나는 팀이 된다.
    """
    base, extra = divmod(total, len(TEAMS))
    fixed_count = {team: 0 for team in TEAMS}
    for team in fixed.values():
        fixed_count[team] += 1

    over = [t for t in TEAMS if fixed_count[t] > base]
    if any(fixed_count[t] > base + 1 for t in TEAMS) or len(over) > extra:
        raise ValueError(
            "고정 배치 인원이 팀 정원을 넘습니다. "
            f"(팀당 {base}명, {extra}개 팀만 {base + 1}명)"
        )

    others = [t for t in TEAMS if t not in over]
    big = over + rng.sample(others, extra - len(over))
    return {t: base + (1 if t in big else 0) for t in TEAMS}


def assign_teams(groups, fixed=None, rng=random):
    """
    묶음(4~5명)마다 학생을 A, B, C, D팀에 한 명씩 랜덤 배치한다.
    5명 묶음에서는 남은 자리가 가장 많은 팀에 한 명이 더 들어간다.

    fixed: {이름: 팀} 형태로 주면 해당 학생은 그 팀에 고정된다.
    고정 학생이 있는 묶음에서는 나머지 학생이 남은 팀으로 랜덤 배치되며,
    팀 정원(10명/11명)은 항상 지켜진다.
    """
    fixed = dict(fixed or {})
    names = [n for g in groups for n in g]
    unknown = [n for n in fixed if n not in names]
    if unknown:
        raise ValueError(f"명단에 없는 학생입니다: {', '.join(unknown)}")
    bad = [t for t in fixed.values() if t not in TEAMS]
    if bad:
        raise ValueError(f"팀은 {', '.join(TEAMS)} 중 하나여야 합니다: {', '.join(bad)}")

    capacity = team_capacities(len(names), fixed, rng)
    # 아직 배치되지 않은 고정 학생 수 (그만큼 자리를 비워 둔다)
    reserved = {team: 0 for team in TEAMS}
    for team in fixed.values():
        reserved[team] += 1

    teams = {team: [] for team in TEAMS}

    def room(t):
        return capacity[t] - len(teams[t]) - reserved[t]

    def pick_roomiest(candidates):
        # 남은 자리가 가장 많은 팀 중에서 랜덤 선택 -> 팀 인원이 끝까지 고르게 유지됨
        best = max(room(t) for t in candidates)
        return rng.choice([t for t in candidates if room(t) == best])

    for group in groups:
        used = set()

        for name in group:
            if name in fixed:
                team = fixed[name]
                teams[team].append(name)
                reserved[team] -= 1
                used.add(team)

        free = [n for n in group if n not in fixed]
        rng.shuffle(free)
        for name in free:
            open_teams = [t for t in TEAMS if room(t) > 0]
            preferred = [t for t in open_teams if t not in used]
            team = pick_roomiest(preferred or open_teams)
            teams[team].append(name)
            used.add(team)

    return teams


def parse_fixed(items):
    """['김제민=A', ...] 형태의 문자열을 {이름: 팀} 딕셔너리로 변환한다."""
    fixed = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"'이름=팀' 형식으로 입력하세요: {item}")
        name, team = (x.strip() for x in item.rsplit("=", 1))
        fixed[name] = team.upper()
    return fixed


def input_fixed_interactively(names):
    """고정 배치할 학생을 입력받는다."""
    print("\n특정 팀에 고정할 학생이 있으면 '이름=팀' 형식으로 입력하세요. (예: 김제민=A)")
    print("여러 명은 쉼표로 구분하고, 없으면 그냥 엔터를 누르세요.")
    while True:
        line = input("고정 배치: ").strip()
        if not line:
            return {}
        try:
            fixed = parse_fixed(parse_names(line))
            missing = [n for n in fixed if n not in names]
            if missing:
                raise ValueError(f"명단에 없는 학생입니다: {', '.join(missing)}")
            bad = [t for t in fixed.values() if t not in TEAMS]
            if bad:
                raise ValueError(f"팀은 {', '.join(TEAMS)} 중 하나여야 합니다.")
            return fixed
        except ValueError as e:
            print(f"  -> {e} 다시 입력하세요.")


def print_teams(teams, fixed=None):
    fixed = fixed or {}
    print("\n========== 팀 편성 결과 ==========")
    for team in TEAMS:
        members = teams[team]
        print(f"\n[{team}팀] {len(members)}명")
        for idx, name in enumerate(members, 1):
            mark = " (고정)" if name in fixed else ""
            print(f"  {idx:2d}. {name}{mark}")
    print("\n==================================")
    print(f"총 인원: {sum(len(m) for m in teams.values())}명")


def main():
    parser = argparse.ArgumentParser(description="학생들을 A, B, C, D팀으로 랜덤 배치합니다.")
    parser.add_argument("file", nargs="?", help="학생 이름 파일 (한 줄에 4~5명 쉼표 구분, 또는 한 줄에 한 명)")
    parser.add_argument("--seed", type=int, help="랜덤 시드 (같은 결과를 다시 얻고 싶을 때)")
    parser.add_argument("--fix", action="append", default=[], metavar="이름=팀",
                        help="특정 학생을 팀에 고정 (예: --fix 김제민=A, 여러 번 사용 가능)")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            groups = parse_groups(f.read())
        names = [n for g in groups for n in g]
        if len(names) != TOTAL_STUDENTS:
            print(f"경고: 이름이 {len(names)}명입니다. (예상 인원: {TOTAL_STUDENTS}명)", file=sys.stderr)
        if len(set(names)) != len(names):
            print("오류: 중복된 이름이 있습니다.", file=sys.stderr)
            sys.exit(1)
    else:
        groups = input_groups_interactively()
        names = [n for g in groups for n in g]

    try:
        groups = normalize_groups(groups)
        fixed = parse_fixed(args.fix)
        if not args.file and not fixed:
            fixed = input_fixed_interactively(names)
        teams = assign_teams(groups, fixed, rng)
    except ValueError as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)

    print_teams(teams, fixed)


if __name__ == "__main__":
    main()
