import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { formatIndianCurrency } from '../utils/currency';

interface FinancialHealthGraphProps {
    data: any[];
}

const FinancialHealthGraph: React.FC<FinancialHealthGraphProps> = ({ data }) => {
    return (
        <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
                <AreaChart
                    data={data}
                    margin={{
                        top: 10,
                        right: 30,
                        left: 0,
                        bottom: 0,
                    }}
                >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="year" />
                    <YAxis tickFormatter={(value) => formatIndianCurrency(value)} />
                    <Tooltip 
                        formatter={(value: number, name: string) => [formatIndianCurrency(value), name]}
                        labelFormatter={(label) => `Year: ${label}`}
                    />
                    <Legend />
                    {/* Stacked Expenses */}
                    <Area type="monotone" dataKey="expenses_needs" stackId="1" stroke="#ff4d4d" fill="#ff4d4d" name="Needs (Survival)" />
                    <Area type="monotone" dataKey="expenses_wants" stackId="1" stroke="#ffc107" fill="#ffc107" name="Wants (Lifestyle)" />
                    
                    {/* Passive Income Overlay */}
                    <Area type="monotone" dataKey="passive_income" stackId="2" stroke="#28a745" fill="#28a745" fillOpacity={0.3} name="Passive Income" />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};

export default FinancialHealthGraph;
