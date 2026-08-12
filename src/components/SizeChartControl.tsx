"use client";

import { useId, useMemo, useState } from "react";
import type {  ProductSizeChart  } from "@/data/product-types";

type ChartLike = {
  id: string;
  titleKo: string;
  noteKo: string;
  headers: string[];
  rows: string[][];
  tabs?: {
    id: string;
    labelKo: string;
    headers: string[];
    rows: string[][];
  }[];
};

export function SizeChartControl({ chart }: { chart: ChartLike | ProductSizeChart }) {
  const [open, setOpen] = useState(false);
  const tabs = chart.tabs?.length ? chart.tabs : null;
  const [tabId, setTabId] = useState(tabs?.[0]?.id ?? "");
  const titleId = useId();

  const active = useMemo(() => {
    if (!tabs) {
      return { headers: chart.headers, rows: chart.rows };
    }
    const found = tabs.find((t) => t.id === tabId) ?? tabs[0];
    return { headers: found.headers, rows: found.rows };
  }, [tabs, tabId, chart.headers, chart.rows]);

  return (
    <div className="size-chart">
      <button
        type="button"
        className="size-chart__trigger"
        onClick={() => setOpen(true)}
      >
        사이즈 차트 보기
      </button>

      {open ? (
        <div
          className="size-chart-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby={titleId}
          onClick={() => setOpen(false)}
        >
          <div
            className="size-chart-modal__panel"
            onClick={(e) => e.stopPropagation()}
          >
            <header className="size-chart-modal__head">
              <div>
                <p className="size-chart-modal__eyebrow">Size Guide</p>
                <h2 id={titleId}>{chart.titleKo}</h2>
              </div>
              <button
                type="button"
                className="size-chart-modal__close"
                aria-label="닫기"
                onClick={() => setOpen(false)}
              >
                ×
              </button>
            </header>
            <p className="size-chart-modal__note">{chart.noteKo}</p>
            {tabs ? (
              <div className="size-chart-modal__tabs" role="tablist">
                {tabs.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    role="tab"
                    aria-selected={t.id === (tabId || tabs[0].id)}
                    className={
                      t.id === (tabId || tabs[0].id)
                        ? "size-chart-modal__tab is-active"
                        : "size-chart-modal__tab"
                    }
                    onClick={() => setTabId(t.id)}
                  >
                    {t.labelKo}
                  </button>
                ))}
              </div>
            ) : null}
            <div className="size-chart-modal__table-wrap">
              <table className="size-chart-table">
                <thead>
                  <tr>
                    {active.headers.map((h) => (
                      <th key={h} scope="col">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {active.rows.map((row) => (
                    <tr key={row.join("-")}>
                      {row.map((cell, i) => (
                        <td key={`${row[0]}-${i}`}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button
              type="button"
              className="btn btn-solid size-chart-modal__done"
              onClick={() => setOpen(false)}
            >
              확인
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
