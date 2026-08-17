import type { ProProfile, SwingMetrics } from "./types";

/**
 * @purego1f (Pure Golf) 스타일의 슬로모션 투어 스윙 아카이브에서
 * 공개된 페이스온·다운더라인 패턴을 지식 베이스로 증류한 템플릿.
 *
 * Instagram은 비공식 스크래핑을 허용하지 않아 원본 릴을 받아 학습하지 않는다.
 * 대신 해당 계정이 반복적으로 보여주는 카메라 앵글(FO / DTL)과
 * 투어 선수별 공개 스윙 특성(회전량, 템포, 임팩트 모양)을 수치화했다.
 *
 * 참고: https://www.instagram.com/purego1f
 */
const tourBlend: SwingMetrics = {
  shoulderTurn: 88,
  hipTurn: 48,
  xFactor: 42,
  spineTilt: 86,
  headStability: 90,
  weightShift: 84,
  clubPath: 82,
  lag: 86,
  posture: 88,
  tempo: 85,
};

export const PROS: ProProfile[] = [
  {
    id: "puregolf-tour",
    name: "Pure Golf Tour Model",
    nameKo: "퓨어골프 투어 모델",
    tour: "Archive",
    role: "@purego1f 슬로모션 아카이브에서 증류한 평균 투어 스윙",
    signature:
      "페이스온·다운더라인 양쪽에서 머리가 고정되고, 탑에서 폭이 유지되며 임팩트에서 핸들이 볼보다 앞선다.",
    whyMatch:
      "특정 선수 카피가 아니라 ‘투어가 공통으로 지키는 선’을 기준으로 보고 싶을 때.",
    instagram: "https://www.instagram.com/purego1f",
    metrics: tourBlend,
    phaseCues: {
      address: "볼은 왼쪽 귀 아래, 무릎·엉덩이·어깨가 타깃 방향으로 살짝 열린 느낌보다 스퀘어.",
      takeaway: "클럽·손·가슴이 한 덩어리로 낮고 길게. 헤드가 손보다 먼저 안쪽으로 말리지 않게.",
      top: "리드 팔이 접히지 않고 폭을 유지. 골반은 어깨보다 적게 돌아 X-팩터가 생긴다.",
      transition: "하체가 먼저 타깃으로. 손이 캐스팅되지 않게 각도를 남겨 둔다.",
      impact: "핸들 포워드, 골반은 열리고 가슴은 아직 볼을 바라보는 쪽.",
      finish: "벨트 버클이 타깃, 무게는 리드 발 뒤꿈치 쪽. 척추 각이 일어서서 뒤집히지 않게.",
    },
    sources: [
      {
        id: "pg-fo-dtl-pair",
        title: "FO + DTL 페어 슬로모션 (아카이브 패턴)",
        angle: "both",
        learned:
          "같은 스윙을 앞·뒤에서 올리면 머리 흔들림과 얼리 익스텐션이 3D에서 바로 드러난다.",
      },
      {
        id: "pg-impact-hold",
        title: "임팩트 홀드 컷",
        angle: "face-on",
        learned: "투어 임팩트는 손-볼-헤드 순서가 아니라 손-볼, 헤드는 아직 릴리스 중.",
      },
    ],
  },
  {
    id: "rory-mcilroy",
    name: "Rory McIlroy",
    nameKo: "로리 맥길로이",
    tour: "PGA",
    role: "와이드 아크 · 공격적인 하체 클리어런스",
    signature:
      "넓은 스탠스와 큰 어깨 회전, 다운에서 골반이 빠르게 비워지며 리드 손목이 약간 굴곡.",
    whyMatch: "비거리를 늘리고 큰 아크·강한 하체 사용을 배우고 싶을 때.",
    metrics: {
      shoulderTurn: 94,
      hipTurn: 52,
      xFactor: 46,
      spineTilt: 84,
      headStability: 86,
      weightShift: 90,
      clubPath: 80,
      lag: 88,
      posture: 82,
      tempo: 78,
    },
    phaseCues: {
      address: "스탠스가 넓고 오른발은 살짝 오픈. 압은 볼 쪽에 모은 느낌.",
      takeaway: "헤드가 낮고 길게, 손이 일찍 안쪽으로 말리지 않음.",
      top: "어깨가 턱 밑까지. 리드 팔이 펴진 채 폭이 산다.",
      transition: "왼쪽 엉덩이가 빠르게 타깃 뒤로 비워진다.",
      impact: "골반은 이미 열리고 핸들은 앞. 오른발 뒤꿈치가 일찍 뜬다.",
      finish: "높은 피니시, 무게는 완전히 왼발.",
    },
    sources: [
      {
        id: "rory-dtl-wide",
        title: "DTL 와이드 아크 슬로모션",
        angle: "down-the-line",
        learned: "테이크어웨이에서 헤드가 손보다 타깃 반대쪽으로 낮게 밀린다.",
      },
    ],
  },
  {
    id: "scottie-scheffler",
    name: "Scottie Scheffler",
    nameKo: "스카티 셰플러",
    tour: "PGA",
    role: "발놀림이 큰 애슬레틱 시퀀스",
    signature:
      "백스윙에서 오른발이 살아 있고, 다운에서 하체가 깊게 좌측으로 밀리며 페이스는 스퀘어에 가깝다.",
    whyMatch: "교과서 자세보다 ‘발과 지면’으로 타이밍을 맞추는 쪽을 선호할 때.",
    metrics: {
      shoulderTurn: 86,
      hipTurn: 50,
      xFactor: 40,
      spineTilt: 80,
      headStability: 78,
      weightShift: 92,
      clubPath: 84,
      lag: 84,
      posture: 76,
      tempo: 80,
    },
    phaseCues: {
      address: "오른발 뒤꿈치가 가볍게, 준비가 정적이지 않다.",
      takeaway: "클럽이 일찍 닫히지 않게 자연스럽게 올라간다.",
      top: "하체가 이미 타깃 쪽으로 밀리기 시작한다.",
      transition: "발이 먼저, 손이 뒤따른다. 얼리 익스텐션처럼 보여도 각은 유지.",
      impact: "왼쪽 옆으로 깊게 이동. 페이스는 스퀘어.",
      finish: "리드 쪽으로 무게가 모이고, 오른발이 거의 끌리듯 남는다.",
    },
    sources: [
      {
        id: "scottie-footwork",
        title: "FO 풋워크 슬로모션",
        angle: "face-on",
        learned: "머리보다 골반·발의 좌측 이동량이 훨씬 크다.",
      },
    ],
  },
  {
    id: "collin-morikawa",
    name: "Collin Morikawa",
    nameKo: "콜린 모리카와",
    tour: "PGA",
    role: "컴팩트한 아이언 컨트롤",
    signature:
      "짧은 백스윙, 조용한 하체, 임팩트에서 핸들이 높고 페이스 컨트롤이 뛰어나다.",
    whyMatch: "아이언 탄착군과 페이스 컨트롤을 우선할 때.",
    metrics: {
      shoulderTurn: 78,
      hipTurn: 42,
      xFactor: 38,
      spineTilt: 90,
      headStability: 94,
      weightShift: 80,
      clubPath: 88,
      lag: 90,
      posture: 92,
      tempo: 90,
    },
    phaseCues: {
      address: "좁고 정돈된 스탠스. 손이 볼보다 약간 앞.",
      takeaway: "원피스, 헤드가 빨리 꺾이지 않음.",
      top: "짧다. 리드 팔이 과하게 접히지 않음.",
      transition: "하체가 조용히 타깃으로. 손의 캐스팅이 없다.",
      impact: "핸들 포워드가 뚜렷, 가슴이 볼 위에 남는다.",
      finish: "낮고 컨트롤된 피니시.",
    },
    sources: [
      {
        id: "morikawa-iron",
        title: "아이언 FO 임팩트",
        angle: "face-on",
        learned: "탑이 짧아도 X-팩터와 래그는 충분히 남긴다.",
      },
    ],
  },
  {
    id: "xander-schauffele",
    name: "Xander Schauffele",
    nameKo: "잰더 쇼플리",
    tour: "PGA",
    role: "스택드 임팩트 · 교과서 시퀀스",
    signature:
      "백스윙이 깊되 다운에서 상·하체가 순서대로 풀리고, 임팩트에 몸이 볼 위에 쌓인다.",
    whyMatch: "군더더기 없는 ‘기본기 투어 스윙’을 기준으로 삼고 싶을 때.",
    metrics: {
      shoulderTurn: 90,
      hipTurn: 46,
      xFactor: 44,
      spineTilt: 88,
      headStability: 92,
      weightShift: 86,
      clubPath: 86,
      lag: 87,
      posture: 90,
      tempo: 88,
    },
    phaseCues: {
      address: "뉴트럴 그립, 스퀘어 스탠스.",
      takeaway: "클럽이 타깃 라인 안쪽으로 과하게 빠지지 않음.",
      top: "어깨 회전이 충분, 머리는 볼 뒤에 남음.",
      transition: "하체 → 몸통 → 팔 순서.",
      impact: "스택드. 골반과 갈비뼈가 볼 위에.",
      finish: "밸런스 좋은 하이 피니시.",
    },
    sources: [
      {
        id: "xander-stacked",
        title: "DTL 스택드 임팩트",
        angle: "down-the-line",
        learned: "다운에서 머리가 공 쪽으로 던지지 않고 각이 유지된다.",
      },
    ],
  },
  {
    id: "jon-rahm",
    name: "Jon Rahm",
    nameKo: "존 람",
    tour: "PGA",
    role: "스트롱 그립 · 짧은 백스윙 · 폭발적 전환",
    signature:
      "백스윙이 짧고 스트롱 그립이라 페이스가 닫혀 보이지만, 하체가 강하게 리드한다.",
    whyMatch: "큰 백스윙이 부담스럽고 짧은 스윙으로 스피드를 내고 싶을 때.",
    metrics: {
      shoulderTurn: 72,
      hipTurn: 44,
      xFactor: 36,
      spineTilt: 82,
      headStability: 88,
      weightShift: 88,
      clubPath: 78,
      lag: 82,
      posture: 84,
      tempo: 74,
    },
    phaseCues: {
      address: "스트롱 그립, 볼 포지션은 표준보다 살짝 오른쪽에 가깝지 않게.",
      takeaway: "일찍 손목이 힌지. 아크는 컴팩트.",
      top: "짧다. 이미 다운을 준비.",
      transition: "하체가 폭발적으로 타깃. 손이 뒤따른다.",
      impact: "강한 커버, 페이스는 스퀘어~약간 닫힘.",
      finish: "회전이 크고 밸런스가 남는다.",
    },
    sources: [
      {
        id: "rahm-short",
        title: "짧은 백스윙 FO",
        angle: "face-on",
        learned: "탑의 길이보다 전환의 순서가 스피드를 만든다.",
      },
    ],
  },
  {
    id: "nelly-korda",
    name: "Nelly Korda",
    nameKo: "넬리 코다",
    tour: "LPGA",
    role: "부드러운 시퀀스 · 일정한 페이스",
    signature:
      "템포가 일정하고 하체가 조용히 리드하며, 임팩트에서 페이스가 오래 스퀘어로 남는다.",
    whyMatch: "힘보다 타이밍·페이스 컨트롤로 아이언과 드라이버를 맞추고 싶을 때.",
    metrics: {
      shoulderTurn: 84,
      hipTurn: 46,
      xFactor: 40,
      spineTilt: 88,
      headStability: 93,
      weightShift: 83,
      clubPath: 90,
      lag: 85,
      posture: 90,
      tempo: 94,
    },
    phaseCues: {
      address: "편안한 무릎 플렉스, 그립 압은 낮게.",
      takeaway: "부드러운 원피스.",
      top: "폭이 유지되고 서두르지 않음.",
      transition: "잠시 정지가 느껴질 정도의 템포.",
      impact: "페이스가 볼을 ‘지나가는’ 시간이 길다.",
      finish: "높은 피니시를 끝까지 보유.",
    },
    sources: [
      {
        id: "nelly-tempo",
        title: "템포 슬로모션",
        angle: "both",
        learned: "백스윙과 다운의 비율이 일정하다. 아마추어는 다운이 급하다.",
      },
    ],
  },
];

export function getPro(id: string): ProProfile | undefined {
  return PROS.find((p) => p.id === id);
}

export function defaultProId() {
  return "puregolf-tour";
}
