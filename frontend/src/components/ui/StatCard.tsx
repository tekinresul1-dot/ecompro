import { cn } from '@/lib/utils';

interface StatCardProps {
    title: string;
    value: string;
    subtitle?: string;
    valueColor?: string;
    icon?: React.ReactNode;
    isLoading?: boolean;
}

export function StatCard({
    title,
    value,
    subtitle,
    valueColor,
    icon,
    isLoading = false,
}: StatCardProps) {
    return (
        <div className="stat-card">
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm text-slate-500">{title}</p>
                    {isLoading ? (
                        <div className="h-8 w-24 bg-slate-200 rounded animate-pulse mt-1" />
                    ) : (
                        <p className={cn('stat-value', valueColor)}>{value}</p>
                    )}
                    {subtitle && <p className="stat-label">{subtitle}</p>}
                </div>
                {icon && (
                    <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center text-primary-500">
                        {icon}
                    </div>
                )}
            </div>
        </div>
    );
}
