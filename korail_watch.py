import os, time, requests
from korail2 import Korail, TrainType, NoResultsError

# ===== 조건 (필요하면 여기만 수정) =====

DEP, ARR = “동대구”, “천안아산”
DATE = “20260927”          # YYYYMMDD
FROM_H, TO_H = “050000”, “110000”
TRAIN = TrainType.KTX

# =====================================

KORAIL_ID = os.environ[“KORAIL_ID”]
KORAIL_PW = os.environ[“KORAIL_PW”]
NTFY_TOPIC = os.environ[“NTFY_TOPIC”]
RUN_HOURS = 5.4            # GitHub Actions 잡 최대 6시간
INTERVAL = 30              # 초

def notify(msg):
requests.post(
f”https://ntfy.sh/{NTFY_TOPIC}”,
data=msg.encode(“utf-8”),
headers={“Title”: “KTX 빈자리”, “Priority”: “high”, “Tags”: “train”},
timeout=10,
)

def main():
k = Korail(KORAIL_ID, KORAIL_PW)
notify(f”감시 시작: {DEP}→{ARR} {DATE} {FROM_H[:2]}~{TO_H[:2]}시”)
seen = {}
deadline = time.time() + RUN_HOURS * 3600

```
while time.time() < deadline:
    try:
        trains = k.search_train(
            DEP, ARR, DATE, FROM_H, train_type=TRAIN, include_no_seats=True
        )
    except NoResultsError:
        trains = []
    except Exception as e:
        print("조회 오류:", e)
        time.sleep(60)
        continue

    for t in trains:
        if t.dep_time > TO_H:
            continue
        key = t.train_no
        avail = t.has_seat()
        if avail and not seen.get(key):
            g = "O" if t.has_general_seat() else "X"
            s = "O" if t.has_special_seat() else "X"
            notify(
                f"{t.train_type_name} {t.train_no}편 "
                f"{t.dep_time[:2]}:{t.dep_time[2:4]} 출발  일반{g} 특실{s}\n"
                f"코레일톡에서 바로 예매!"
            )
        seen[key] = avail
    print(time.strftime("%H:%M:%S"), "checked", len(trains))
    time.sleep(INTERVAL)

notify("감시 종료(시간 만료). 필요하면 다시 실행.")
```

if **name** == “**main**”:
main()
