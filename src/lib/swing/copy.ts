import { METRIC_LABEL_KO } from "./types";
import type { MetricKey, ProProfile } from "./types";

type Copy = { summary: string; drill: string; feel: string };

const COPY: Record<MetricKey, { low: Copy; high: Copy }> = {
  shoulderTurn: {
    low: {
      summary: "백스윙에서 어깨 회전이 프로보다 작아 아크가 짧고 스피드가 손에서 나기 쉽습니다.",
      drill: "얼라인먼트 스틱을 어깨에 얹고 천천히 어깨만 90°까지 감았다가 풀기 (거울 앞 10회).",
      feel: "턱 밑으로 왼쪽 어깨가 들어오는 느낌. 팔로 올리지 말 것.",
    },
    high: {
      summary: "어깨가 과회전하며 탑에서 스웨이가 생기거나 페이스가 열리기 쉽습니다.",
      drill: "오른발 바깥에 의자를 두고 힙이 밀리지 않게 어깨만 감는 하프 스윙.",
      feel: "오른쪽 허벅지 안쪽에 압을 남긴 채 상체만 돌린다.",
    },
  },
  hipTurn: {
    low: {
      summary: "골반 회전이 부족해 상체만 돌고, 다운에서 팔이 아웃-인으로 떨어지기 쉽습니다.",
      drill: "양손에 클럽을 가로로 잡고 골반만 좌우로 45° 회전 (발바닥 압 느끼며 12회).",
      feel: "벨트 버클이 먼저 움직이고 가슴은 늦게.",
    },
    high: {
      summary: "골반이 먼저 너무 열리면 얼리 익스텐션·슬라이스가 함께 오기 쉽습니다.",
      drill: "백스윙 탑에서 1초 정지 후 골반을 타깃으로 10cm만 밀고 멈추기.",
      feel: "열지 말고 ‘옮긴다’. 회전은 그 다음.",
    },
  },
  xFactor: {
    low: {
      summary: "어깨와 골반이 같이 돌아가 꼬임이 없습니다. 비거리와 페이스 컨트롤이 함께 떨어집니다.",
      drill: "발은 고정, 골반은 적게, 어깨만 더 감는 ‘분리 스윙’ 슬로모 8회.",
      feel: "옆구리가 늘어나는 감각을 탑에서 1초 유지.",
    },
    high: {
      summary: "분리가 과하면 허리 부담과 타이밍 붕괴가 옵니다. 지금은 조금 줄여도 됩니다.",
      drill: "하프 스윙으로 어깨·골반이 함께 풀리게 템포 3:1로 맞추기.",
      feel: "꼬임을 ‘버티지’ 말고 하체가 먼저 풀어 주게.",
    },
  },
  spineTilt: {
    low: {
      summary: "어드레스의 척추 각이 다운에서 일어섭니다. 토핑·슬라이스·뒷땅의 공통 원인입니다.",
      drill: "엉덩이 뒤에 의자를 두고 다운 내내 의자를 밀어내는 하프 스윙 15개.",
      feel: "머리가 공 위로 던지지 않고, 엉덩이가 뒤로 남는다.",
    },
    high: {
      summary: "숙임이 과하면 탄도가 낮고 페이스가 닫히기 쉽습니다.",
      drill: "턱과 가슴 사이 주먹 하나 공간을 유지한 채 웨이브 드릴.",
      feel: "가슴이 공을 ‘눌러’ 버리지 않게.",
    },
  },
  headStability: {
    low: {
      summary: "머리가 좌우·상하로 많이 움직입니다. 로리·모리카와 아카이브와 가장 크게 갈리는 지점입니다.",
      drill: "볼 뒤에 얼라인먼트 스틱을 세우고 머리와 스틱 간격을 유지한 채 슬로모 스윙.",
      feel: "코가 볼 뒤에 남아 있는 시간을 늘린다.",
    },
    high: {
      summary: "머리 고정은 좋습니다. 다만 고개가 잠기면 회전이 죽을 수 있으니 턱만 살짝 열어 두세요.",
      drill: "피니시까지 턱이 타깃 쪽 어깨 위에 자연히 올라오게 마무리 10회.",
      feel: "고정은 ‘얼음’이 아니라 ‘축이 안 무너짐’.",
    },
  },
  weightShift: {
    low: {
      summary: "체중이 오른발에 남는 리버스 피벗/행백입니다. 임팩트에서 뜨거나 슬라이스가 납니다.",
      drill: "백스윙 후 왼발 뒤꿈치로 땅을 먼저 밟고 다운 (스텝스루 8회).",
      feel: "왼쪽 허벅지 안쪽이 임팩트 전에 이미 단단하다.",
    },
    high: {
      summary: "타깃 쪽으로 너무 빨리 밀리면 스웨이입니다. 회전 없이 밀기만 하는 패턴입니다.",
      drill: "오른발 안쪽에 수건을 두고 백스윙에서 수건을 밟은 채 유지.",
      feel: "이동은 왼쪽 ‘옆’이지 왼쪽 ‘위’가 아니다.",
    },
  },
  clubPath: {
    low: {
      summary: "아웃-인 패스입니다. 오버더탑이 의심됩니다. DTL에서 손이 머리 밖으로 떨어집니다.",
      drill: "헤드 바깥에 헤드커버를 두고 그걸 안 치게 인사이드로 내려오기 12개.",
      feel: "오른쪽 주머니 쪽으로 손이 떨어진다.",
    },
    high: {
      summary: "인-아웃이 과하면 푸시·훅이 나옵니다. 패스를 조금 뉴트럴로.",
      drill: "타깃 라인에 스틱, 다운에서 헤드가 스틱과 평행에 가깝게.",
      feel: "몸을 열어 던지지 말고 가슴이 볼을 본 채 패스만 교정.",
    },
  },
  lag: {
    low: {
      summary: "탑에서 이미 손목 각이 풀립니다(캐스팅). 프로 슬로모션의 임팩트 홀드와 반대입니다.",
      drill: "9시-3시 스윙에서 오른손 중지·약지로 각도를 유지한 채 임팩트만 통과.",
      feel: "손이 볼 앞에 있고 헤드는 아직 뒤.",
    },
    high: {
      summary: "래그가 과하면 블로된 샷·우측 미스가 납니다. 릴리스를 허용하세요.",
      drill: "피니시에서 클럽이 등을 감싸게 풀어서 마무리하는 스윙 10개.",
      feel: "임팩트 직후 오른쪽 손바닥이 땅을 보도록.",
    },
  },
  posture: {
    low: {
      summary: "다운에서 골반이 타깃 쪽으로 밀려 일어섭니다(얼리 익스텐션). 3D에서 가장 잘 보입니다.",
      drill: "벽에서 한 뼘 떨어뜨려 엉덩이가 벽에 남게 하프 스윙 15개.",
      feel: "벨트가 타깃이 아니라 ‘앞-아래’를 유지.",
    },
    high: {
      summary: "너무 웅크리면 회전이 막힙니다. 무릎 플렉스를 조금 펴 주세요.",
      drill: "어드레스에서 무릎을 5°만 펴고 같은 높이로 스윙.",
      feel: "앉지 말고 ‘기울인 채 돈다’.",
    },
  },
  tempo: {
    low: {
      summary: "다운이 급합니다. 넬리·모리카와 아카이브는 백스윙:다운 ≈ 3:1입니다.",
      drill: "속으로 ‘1-2-3 / 1’ 카운트. 얼라인먼트 스틱 스윙 20개.",
      feel: "탑에서 서두르지 않고 하체만 먼저.",
    },
    high: {
      summary: "템포가 느리면 전환에서 힘이 빠집니다. 전환만 조금 빠르게.",
      drill: "숏백스윙 후 다운만 가볍게 가속하는 9시-3시.",
      feel: "느린 백, 부드러운 가속. 급하지 않게.",
    },
  },
};

export function gapCopy(
  key: MetricKey,
  user: number,
  pro: number,
): Copy {
  const side = user < pro ? "low" : "high";
  return COPY[key][side];
}

export function phaseNote(
  pro: ProProfile,
  phase: keyof ProProfile["phaseCues"],
  userHint: string,
) {
  return `${pro.phaseCues[phase]} ${userHint}`.trim();
}

export function trialSummaryLines(
  proName: string,
  overall: number,
  top: { key: MetricKey; summary: string; drill: string }[],
) {
  const lines = [
    `${proName} 대비 유사도 ${overall}점.`,
    ...top.map(
      (g, i) =>
        `${i + 1}. ${METRIC_LABEL_KO[g.key]} — ${g.summary} 바로 할 것: ${g.drill}`,
    ),
  ];
  return lines;
}
