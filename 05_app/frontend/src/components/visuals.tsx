// Visuals: Plotly charts (figures built by the backend), the supply-network map (deck.gl on a dark basemap) and the
// interactive SVG canvas (plant floor + Impact Web).
import { useEffect, useMemo, useRef } from "react";
import createPlotlyComponent from "react-plotly.js/factory";
// @ts-expect-error — the basic Plotly bundle (scatter, bar, pie: all our charts need) ships without types
import Plotly from "plotly.js-basic-dist-min";
import DeckGL from "@deck.gl/react";
import { ArcLayer, ScatterplotLayer, TextLayer } from "@deck.gl/layers";
import { Map as BaseMap } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Figure, Network } from "../api";
import { mountCanvas } from "../canvas/kkCanvas.js";
import "../canvas/kkCanvas.css";

const Plot = createPlotlyComponent(Plotly);

export function Chart({ figure, height }: { figure: Figure; height?: number }) {
  const layout = useMemo(() => ({ ...figure.layout, autosize: true, ...(height ? { height } : {}) }), [figure, height]);
  return (
    <section className="card" style={{ padding: "14px 16px 10px" }}>
      <Plot data={figure.data as Plotly.Data[]} layout={layout} config={{ displaylogo: false, responsive: true, displayModeBar: "hover" }}
            useResizeHandler style={{ width: "100%" }} />
    </section>
  );
}

const BASEMAP = "https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json";

/** Suppliers → plants → distribution centers. Clicking a plant calls onPlant. */
export function NetworkMap({ data, height = 440, onPlant }: { data: Network; height?: number; onPlant?: (id: string) => void }) {
  const crit = data.plants.filter(p => p.status === "critical");
  const layers = [
    new ArcLayer({ id: "arcs", data: data.arcs, getSourcePosition: d => d.from as [number, number], getTargetPosition: d => d.to as [number, number],
                   getSourceColor: d => (d.hot ? [214, 40, 57, 230] : [156, 195, 255, 70]), getTargetColor: d => (d.hot ? [214, 40, 57, 230] : [156, 195, 255, 70]),
                   getWidth: d => d.width, getHeight: 0.35, pickable: true }),
    new ScatterplotLayer({ id: "suppliers", data: data.suppliers, getPosition: d => [d.lon, d.lat], getFillColor: d => d.color as [number, number, number],
                           getRadius: 45000, radiusMinPixels: 3, radiusMaxPixels: 7, pickable: true }),
    new ScatterplotLayer({ id: "dcs", data: data.dcs, getPosition: d => [d.lon, d.lat], getFillColor: d => d.color as [number, number, number],
                           getLineColor: [255, 255, 255], lineWidthMinPixels: 2, stroked: true, getRadius: 90000, radiusMinPixels: 6, radiusMaxPixels: 12, pickable: true }),
    new ScatterplotLayer({ id: "halo", data: crit, getPosition: d => [d.lon, d.lat], getFillColor: [214, 40, 57, 50], getRadius: 260000,
                           radiusMinPixels: 14, radiusMaxPixels: 34 }),
    new ScatterplotLayer({ id: "plants", data: data.plants, getPosition: d => [d.lon, d.lat], getFillColor: d => d.color as [number, number, number],
                           getLineColor: [255, 255, 255], lineWidthMinPixels: 3, stroked: true, getRadius: 130000, radiusMinPixels: 11,
                           radiusMaxPixels: 20, pickable: true, onClick: info => { if (info.object) onPlant?.(info.object.id); } }),
    new TextLayer({ id: "labels", data: data.plants, getPosition: d => [d.lon, d.lat], getText: d => d.id, getSize: 15,
                    getColor: [255, 255, 255], getPixelOffset: [0, -28] }),
    new TextLayer({ id: "dclabels", data: data.dcs, getPosition: d => [d.lon, d.lat], getText: d => d.id, getSize: 11,
                    getColor: [185, 198, 218], getPixelOffset: [0, 20] }),
  ];
  return (
    <div style={{ position: "relative", height, borderRadius: 12, overflow: "hidden" }}>
      <DeckGL initialViewState={{ latitude: 30, longitude: -22, zoom: 1.15, pitch: 30 }} controller layers={layers}
              getCursor={({ isHovering }) => (isHovering ? "pointer" : "grab")}
              getTooltip={({ object }) => object && { html: `<b>${object.name || object.id || ""}</b><br/>${object.tip}`, className: "maptip",
                                                      style: { background: "#0A1F44", color: "#fff", fontSize: "12px", borderRadius: "8px" } }}>
        <BaseMap mapStyle={BASEMAP} />
      </DeckGL>
    </div>
  );
}

/** The SVG canvas. `scene` is the backend's floor or web scene; clicks come back as {kind, id, line?}. */
export function SceneCanvas({ scene, onSelect }: { scene: Record<string, unknown>; onSelect: (s: { kind: string; id: string; line?: string }) => void }) {
  const host = useRef<HTMLDivElement>(null);
  const cb = useRef(onSelect);
  cb.current = onSelect;                 // the canvas keeps one callback; this keeps it pointing at the latest handler
  useEffect(() => {
    if (host.current)
      mountCanvas({ data: scene, parentElement: host.current,
                    setTriggerValue: (_name: string, value: { kind: string; id: string; line?: string }) => cb.current(value) });
  }, [scene]);
  return <div ref={host} />;
}
