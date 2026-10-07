import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { AnalyticsMetrics } from "../api/analytics";
import { formatCost, formatLatency, formatTokens } from "../utils/formatters";

interface Props {
  data: (AnalyticsMetrics & { model: string })[];
}

// Categorical palette, validated for the dark surface this app uses
// (scripts/validate_palette.js, --mode dark: lightness band, chroma floor,
// CVD separation and normal-vision separation all pass for this order).
// All three charts below index into this with the SAME `data` array and the
// SAME index (no per-chart offset), so a given model keeps the same color
// in every chart - previously each chart offset its index by one more than
// the last, so the same model showed a different color in each chart.
const colors = ["#3987e5", "#d95926", "#199e70", "#9085e9"];

const CustomTooltip = ({ active, payload, label, formatter }: any) => {
  if (active && payload && payload.length) {
    return (
      <div
        style={{
          backgroundColor: "var(--color-bg-elevated)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-md)",
          padding: "var(--space-3)",
          boxShadow: "var(--shadow-md)",
          color: "var(--color-text-primary)",
        }}
      >
        <p style={{ fontWeight: 600, marginBottom: "4px" }}>{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <div
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: entry.color,
              }}
            />
            <span style={{ color: "var(--color-text-secondary)" }}>
              {entry.name}:
            </span>
            <span style={{ fontWeight: 500 }}>
              {formatter ? formatter(entry.value) : entry.value}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export default function ModelCharts({ data }: Props) {
  if (!data || data.length === 0) return null;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "var(--space-6)", marginTop: "var(--space-6)" }}>
      {/* Chart 1: Requests by Model */}
      <div className="card" style={{ padding: "var(--space-4)" }}>
        <h3 style={{ fontSize: "14px", fontWeight: 600, marginBottom: "var(--space-4)", color: "var(--color-text-secondary)" }}>
          Requests by Model
        </h3>
        <div style={{ width: "100%", height: 250 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis 
                dataKey="model" 
                stroke="var(--color-text-secondary)" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false}
                dy={10}
              />
              <YAxis 
                stroke="var(--color-text-secondary)" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false}
                tickFormatter={(val) => formatTokens(val)}
              />
              <Tooltip content={<CustomTooltip formatter={(val: number) => formatTokens(val)} />} cursor={{ fill: "var(--color-bg-tertiary)", opacity: 0.4 }} />
              <Bar dataKey="request_volume" name="Requests" radius={[4, 4, 0, 0]}>
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 2: Total Cost by Model */}
      <div className="card" style={{ padding: "var(--space-4)" }}>
        <h3 style={{ fontSize: "14px", fontWeight: 600, marginBottom: "var(--space-4)", color: "var(--color-text-secondary)" }}>
          Total Cost by Model
        </h3>
        <div style={{ width: "100%", height: 250 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis 
                dataKey="model" 
                stroke="var(--color-text-secondary)" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false}
                dy={10}
              />
              <YAxis 
                stroke="var(--color-text-secondary)" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false}
                tickFormatter={(val) => formatCost(val)}
              />
              <Tooltip content={<CustomTooltip formatter={(val: number) => formatCost(val)} />} cursor={{ fill: "var(--color-bg-tertiary)", opacity: 0.4 }} />
              <Bar dataKey="total_cost" name="Cost" radius={[4, 4, 0, 0]}>
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 3: P95 Latency by Model */}
      <div className="card" style={{ padding: "var(--space-4)" }}>
        <h3 style={{ fontSize: "14px", fontWeight: 600, marginBottom: "var(--space-4)", color: "var(--color-text-secondary)" }}>
          P95 Latency by Model
        </h3>
        <div style={{ width: "100%", height: 250 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis 
                dataKey="model" 
                stroke="var(--color-text-secondary)" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false}
                dy={10}
              />
              <YAxis 
                stroke="var(--color-text-secondary)" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false}
                tickFormatter={(val) => `${val}ms`}
              />
              <Tooltip content={<CustomTooltip formatter={(val: number) => formatLatency(val)} />} cursor={{ fill: "var(--color-bg-tertiary)", opacity: 0.4 }} />
              <Bar dataKey="p95_latency_ms" name="P95 Latency" radius={[4, 4, 0, 0]}>
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
