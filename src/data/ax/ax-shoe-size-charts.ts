/** Arc'teryx footwear UK sizing chart (official GB help/sizing/footwear). */
export type ShoeSizeChart = {
  id: string;
  titleKo: string;
  noteKo: string;
  headers: string[];
  rows: string[][];
};

/** Official Arc'teryx footwear conversion — UK is the Briq size picker value. */
const AX_FOOTWEAR_ROWS: string[][] = [
  ["3.5", "22cm", "4", "5", "36", "220mm"],
  ["4", "22.5cm", "4.5", "5.5", "36⅔", "225mm"],
  ["4.5", "23cm", "5", "6", "37⅓", "230mm"],
  ["5", "23.5cm", "5.5", "6.5", "38", "235mm"],
  ["5.5", "24cm", "6", "7", "38⅔", "240mm"],
  ["6", "24.5cm", "6.5", "7.5", "39⅓", "245mm"],
  ["6.5", "25cm", "7", "8", "40", "250mm"],
  ["7", "25.5cm", "7.5", "8.5", "40⅔", "255mm"],
  ["7.5", "26cm", "8", "9", "41⅓", "260mm"],
  ["8", "26.5cm", "8.5", "9.5", "42", "265mm"],
  ["8.5", "27cm", "9", "10", "42⅔", "270mm"],
  ["9", "27.5cm", "9.5", "10.5", "43⅓", "275mm"],
  ["9.5", "28cm", "10", "11", "44", "280mm"],
  ["10", "28.5cm", "10.5", "11.5", "44⅔", "285mm"],
  ["10.5", "29cm", "11", "12", "45⅓", "290mm"],
  ["11", "29.5cm", "11.5", "12.5", "46", "295mm"],
  ["11.5", "30cm", "12", "13", "46⅔", "300mm"],
  ["12", "30.5cm", "12.5", "13.5", "47⅓", "305mm"],
  ["12.5", "31cm", "13", "14", "48", "310mm"],
  ["13", "31.5cm", "13.5", "14.5", "48⅔", "315mm"],
  ["13.5", "32cm", "14", "15", "49⅓", "320mm"],
];

const HEADERS = ["UK", "CM", "US M", "US W", "EU", "KR"];

const NOTE =
  "발 길이를 재어 가장 가깝거나 같거나 큰 수치를 고르세요. Briq 표기 사이즈는 Arc'teryx UK 기준입니다. 일부 모델은 크게 나오는 편이라 반 사이즈 작게 권장될 수 있으니 상품 설명을 확인하세요.";

export const AX_MEN_SHOE_SIZE_CHART: ShoeSizeChart = {
  id: "ax-shoes-mens",
  titleKo: "아크테릭스 남성 슈즈 사이즈 차트 (UK)",
  noteKo: NOTE,
  headers: HEADERS,
  rows: AX_FOOTWEAR_ROWS,
};

export const AX_WOMEN_SHOE_SIZE_CHART: ShoeSizeChart = {
  id: "ax-shoes-womens",
  titleKo: "아크테릭스 여성 슈즈 사이즈 차트 (UK)",
  noteKo: NOTE,
  headers: HEADERS,
  rows: AX_FOOTWEAR_ROWS,
};

export function axShoeSizeChartForCollections(
  collections: string[] | undefined,
): ShoeSizeChart | undefined {
  const cols = collections || [];
  if (cols.some((c) => c === "ax-shoes-mens" || c === "arcteryx-shoes-mens")) {
    return AX_MEN_SHOE_SIZE_CHART;
  }
  if (cols.some((c) => c === "ax-shoes-womens" || c === "arcteryx-shoes-womens")) {
    return AX_WOMEN_SHOE_SIZE_CHART;
  }
  return undefined;
}
