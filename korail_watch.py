import os, time, requests
from korail2 import Korail, TrainType, NoResultsError

# ===== 조건 (필요하면 여기만 수정) =====
DEP, ARR = "동대구", "천안아산"
TRAIN = TrainType.KTX
# (날짜 YYYYMMDD, 시작시각, 끝시각) — 줄 추가/삭제로 조절
WINDOWS = [
    ("20260926", "140000", "240000"),
    ("20260927", "050000", "110000"),
]
# =====================================

KORAIL_ID = os.environ["KORAIL_ID"]
KORAIL_PW = os.environ["KORAIL_PW"]
NTFY_TOPIC = os.environ["NTFY_TOPIC"]
RUN_HOURS = 5.4            # GitHub Actions 잡 최대 6시간
INTERVAL = 30              # 초


def notify(msg):
    requests.post(
        "https://ntfy.sh",
        json={"topic": NTFY_TOPIC, "title": "KTX 빈자리", "message": msg,
              "priority": 5, "tags": ["train"]},
        timeout=10,
    )


def main():
    k = Korail(KORAIL_ID, KORAIL_PW)
    desc = ", ".join(f"{d[4:6]}/{d[6:]} {f[:2]}~{t[:2]}시" for d, f, t in WINDOWS)
    notify(f"감시 시작: {DEP}→{ARR} {desc}")
    seen = {}
    deadline = time.time() + RUN_HOURS * 3600

    while time.time() < deadline:
        total = 0
        for date, from_h, to_h in WINDOWS:
            try:
                trains = k.search_train(
                    DEP, ARR, date, from_h, train_type=TRAIN, include_no_seats=True
                )
            except NoResultsError:
                trains = []
            except Exception as e:
                print("조회 오류:", e)
                time.sleep(60)
                continue

            for t in trains:
                if t.dep_time > to_h:
                    continue
                key = (date, t.train_no)
                avail = t.has_seat()
                if avail and not seen.get(key):
                    g = "O" if t.has_general_seat() else "X"
                    s = "O" if t.has_special_seat() else "X"
                    notify(
                        f"{date[4:6]}/{date[6:]} {t.train_type_name} {t.train_no}편 "
                        f"{t.dep_time[:2]}:{t.dep_time[2:4]} 출발  일반{g} 특실{s}\n"
                        f"코레일톡에서 바로 예매!"
                    )
                seen[key] = avail
            total += len(trains)
            time.sleep(2)
        print(time.strftime("%H:%M:%S"), "checked", total)
        time.sleep(INTERVAL)

    notify("감시 종료(시간 만료). 필요하면 다시 실행.")


if __name__ == "__main__":
    main()
