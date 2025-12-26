'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { formatCurrency, formatPercent } from '@/lib/utils';

interface CostBreakdownChartProps {
    data: any[];
}

const COLORS = [
    '#475569', // Kargo Ücreti - Slate
    '#6366f1', // Komisyon - Indigo
    '#10b981', // Kâr - Emerald
    '#f59e0b', // Net KDV - Amber
    '#8b5cf6', // Platform Bedeli - Purple
    '#ef4444', // Stopaj Kesintisi - Red
    '#3b82f6', // Ürün Maliyeti - Blue
];

export function CostBreakdownChart({ data }: CostBreakdownChartProps) {
    // Use demo data if no data provided
    const chartData = data && data.length > 0 ? data : [
        { name: 'Kargo Ücreti', value: 38.99, color: COLORS[0] },
        { name: 'Komisyon', value: 32.99, color: COLORS[1] },
        { name: 'Kâr', value: 9.23, color: COLORS[2] },
        { name: 'Net KDV', value: 8.81, color: COLORS[3] },
        { name: 'Platform Bedeli', value: 18.33, color: COLORS[4] },
        { name: 'Ürün Maliyeti', value: 0.65, color: COLORS[6] },
    ];

    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-3">
                    <div className="flex items-center gap-2">
                        <span
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: data.color || payload[0].color }}
                        />
                        <span className="text-sm font-medium text-slate-800">{data.name}</span>
                    </div>
                    <p className="text-lg font-bold text-slate-800 mt-1">
                        %{data.value?.toFixed(2)}
                    </p>
                </div>
            );
        }
        return null;
    };

    const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index, name }: any) => {
        const RADIAN = Math.PI / 180;
        const radius = outerRadius * 1.2;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);

        if (percent < 0.05) return null; // Don't show labels for small slices

        return (
            <text
                x={x}
                y={y}
                fill="#64748b"
                textAnchor={x > cx ? 'start' : 'end'}
                dominantBaseline="central"
                fontSize={12}
            >
                {(percent * 100).toFixed(1)}
            </text>
        );
    };

    return (
        <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                        data={chartData}
                        cx="50%"
                        cy="45%"
                        labelLine={false}
                        label={renderCustomizedLabel}
                        outerRadius={80}
                        innerRadius={40}
                        fill="#8884d8"
                        dataKey="value"
                        strokeWidth={2}
                        stroke="#fff"
                    >
                        {chartData.map((entry: any, index: number) => (
                            <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend
                        layout="horizontal"
                        verticalAlign="bottom"
                        align="center"
                        wrapperStyle={{ paddingTop: 10 }}
                        iconType="circle"
                        iconSize={8}
                        formatter={(value, entry: any) => (
                            <span className="text-xs text-slate-600">{value}</span>
                        )}
                    />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
}
