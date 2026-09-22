#!/usr/bin/env python3
"""
그룹과제 팀 편성 프로그램

- 수강생 39명 + 청강생 2명 = 총 41명
- 학생 이름을 4명씩 입력받아, 매 4명을 A, B, C, D팀에 한 명씩 랜덤 배치
- 4명 단위로 나누고 남은 학생(41명이면 1명)은 랜덤한 팀에 배치
  -> 결과: 10명 팀 3개 + 11명 팀 1개

사용법:
    python team_assign.py                 # 4명씩 직접 입력
    python team_assign.py names.txt       # 파일에서 이름 읽기 (한 줄에 한 명 또는 쉼표 구분)
    python team_assign.py names.txt --seed 42   # 결과 재현용 시드 지정
"""

import argparse
import random
import sys

TEAMS = ["A", "B", "C", "D"]
TOTAL_STUDENTS = 41
GROUP_SIZE = len(TEAMS)  # 4명씩 입력/배치


def parse_names(text):
    """쉼표 또는 줄바꿈으로 구분된 이름 목록을 리스트로 변환한다."""
    names = []
    for line in text.splitlines():
        for name in line.split(","):
            name = name.strip()
            if name:
                names.append(name)
    return names


def input_names_interactively(total=TOTAL_STUDENTS):
    """학생 이름을 4명씩 입력받는다."""
    names = []
    print(f"학생 {total}명의 이름을 {GROUP_SIZE}명씩 쉼표(,)로 구분하여 입력하세요.")
    while len(names) < total:
        need = min(GROUP_SIZE, total - len(names))
        round_no = len(names) // GROUP_SIZE + 1
        line = input(f"[{round_no}번째 입력] {need}명 ({len(names)}/{total}): ")
        batch = parse_names(line)
        if len(batch) != need:
            print(f"  -> {need}명을 입력해야 합니다. (입력된 인원: {len(batch)}명) 다시 입력하세요.")
            continue
        duplicated = [n for n in batch if n in names or batch.count(n) > 1]
        if duplicated:
            print(f"  -> 중복된 이름이 있습니다: {', '.join(sorted(set(duplicated)))}. 다시 입력하세요.")
            continue
        names.extend(batch)
    return names


def assign_teams(names, rng=random):
    """
    이름을 4명씩 묶어 각 묶음의 학생을 A, B, C, D팀에 한 명씩 랜덤 배치한다.
    4명으로 나누어 떨어지지 않고 남은 학생은 서로 다른 팀에 랜덤 배치한다.
    """
    teams = {team: [] for team in TEAMS}
    full = len(names) - len(names) % GROUP_SIZE

    for i in range(0, full, GROUP_SIZE):
        group = names[i:i + GROUP_SIZE]
        shuffled_teams = TEAMS[:]
        rng.shuffle(shuffled_teams)
        for name, team in zip(group, shuffled_teams):
            teams[team].append(name)

    leftovers = names[full:]
    for name, team in zip(leftovers, rng.sample(TEAMS, len(leftovers))):
        teams[team].append(name)

    return teams


def print_teams(teams):
    print("\n========== 팀 편성 결과 ==========")
    for team in TEAMS:
        members = teams[team]
        print(f"\n[{team}팀] {len(members)}명")
        for idx, name in enumerate(members, 1):
            print(f"  {idx:2d}. {name}")
    print("\n==================================")
    print(f"총 인원: {sum(len(m) for m in teams.values())}명")


def main():
    parser = argparse.ArgumentParser(description="학생들을 A, B, C, D팀으로 랜덤 배치합니다.")
    parser.add_argument("file", nargs="?", help="학생 이름 파일 (한 줄에 한 명 또는 쉼표 구분)")
    parser.add_argument("--seed", type=int, help="랜덤 시드 (같은 결과를 다시 얻고 싶을 때)")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            names = parse_names(f.read())
        if len(names) != TOTAL_STUDENTS:
            print(f"경고: 이름이 {len(names)}명입니다. (예상 인원: {TOTAL_STUDENTS}명)", file=sys.stderr)
        if len(set(names)) != len(names):
            print("오류: 중복된 이름이 있습니다.", file=sys.stderr)
            sys.exit(1)
    else:
        names = input_names_interactively()

    print_teams(assign_teams(names, rng))


if __name__ == "__main__":
    main()
