/** Burberry adult shoe size charts (KR labels). Sourced from UK size-guide API. */
export type ShoeSizeChart = {
  id: string;
  titleKo: string;
  noteKo: string;
  headers: string[];
  rows: string[][];
};

export const BB_MEN_SHOE_SIZE_CHART: ShoeSizeChart = {
  id: "bb-men-shoes",
  titleKo: "남성 슈즈 사이즈 차트",
  noteKo: "아래 사이즈표를 참고해 가장 잘 맞는 사이즈를 찾아보세요. Briq 표기 사이즈는 영국(UK) 기준입니다.",
  headers: ["UK", "IT", "USA", "JP", "KR"],
  rows: [
    ["5", "39", "6", "25cm", "250mm"],
    ["5.5", "39.5", "6.5", "25.5cm", "255mm"],
    ["6", "40", "7", "26cm", "260mm"],
    ["6.5", "40.5", "7.5", "26.2cm", "262mm"],
    ["7", "41", "8", "26.5cm", "265mm"],
    ["7.5", "41.5", "8.5", "26.7cm", "267mm"],
    ["8", "42", "9", "27cm", "270mm"],
    ["8.5", "42.5", "9.5", "27.5cm", "275mm"],
    ["9", "43", "10", "28cm", "280mm"],
    ["9.5", "43.5", "10.5", "28.2cm", "282mm"],
    ["10", "44", "11", "28.5cm", "285mm"],
    ["10.5", "44.5", "11.5", "28.7cm", "287mm"],
    ["11", "45", "12", "29cm", "290mm"],
    ["11.5", "45.5", "12.5", "29.5cm", "295mm"],
    ["12", "46", "13", "30cm", "300mm"],
  ],
};

export const BB_WOMEN_SHOE_SIZE_CHART: ShoeSizeChart = {
  id: "bb-women-shoes",
  titleKo: "여성 슈즈 사이즈 차트",
  noteKo: "아래 치수를 확인해 사이즈를 선택하세요. Briq 표기 사이즈는 영국(UK) 기준입니다.",
  headers: ["UK", "IT", "USA", "JP", "KR"],
  rows: [
    ["2", "35", "5", "22.5cm", "225mm"],
    ["2.5", "35.5", "5.5", "22.8cm", "228mm"],
    ["3", "36", "6", "23cm", "230mm"],
    ["3.5", "36.5", "6.5", "23.5cm", "235mm"],
    ["4", "37", "7", "24cm", "240mm"],
    ["4.5", "37.5", "7.5", "24.2cm", "242mm"],
    ["5", "38", "8", "24.5cm", "245mm"],
    ["5.5", "38.5", "8.5", "24.8cm", "248mm"],
    ["6", "39", "9", "25cm", "250mm"],
    ["6.5", "39.5", "9.5", "25.5cm", "255mm"],
    ["7", "40", "10", "26cm", "260mm"],
    ["7.5", "40.5", "10.5", "26.2cm", "262mm"],
    ["8", "41", "11", "26.5cm", "265mm"],
    ["8.5", "41.5", "11.5", "26.7cm", "267mm"],
    ["9", "42", "12", "27cm", "270mm"],
  ],
};

export function shoeSizeChartForCollections(
  collections: string[] | undefined,
): ShoeSizeChart | undefined {
  const cols = collections || [];
  const isMenShoe = cols.some(
    (c) =>
      c === "bb-men-shoes" ||
      c.startsWith("bb-men-sneakers") ||
      c.startsWith("bb-men-sandals") ||
      c.startsWith("bb-men-boots") ||
      c.startsWith("bb-men-loafers"),
  );
  if (isMenShoe) return BB_MEN_SHOE_SIZE_CHART;
  const isWomenShoe = cols.some(
    (c) =>
      c === "bb-women-shoes" ||
      c.startsWith("bb-women-sneakers") ||
      c.startsWith("bb-women-sandals") ||
      c.startsWith("bb-women-boots") ||
      c.startsWith("bb-women-loafers") ||
      c.startsWith("bb-women-pumps"),
  );
  if (isWomenShoe) return BB_WOMEN_SHOE_SIZE_CHART;
  return undefined;
}
