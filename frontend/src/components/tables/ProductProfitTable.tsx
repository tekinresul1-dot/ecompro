import { formatCurrency, formatPercent, cn } from '@/lib/utils';

interface Product {
    barcode: string;
    product_name: string;
    total_profit?: string;
    total_loss?: string;
    avg_margin: string;
    quantity_sold: number;
}

interface ProductProfitTableProps {
    products: Product[];
    type: 'profit' | 'loss';
}

export function ProductProfitTable({ products, type }: ProductProfitTableProps) {
    if (products.length === 0) {
        return (
            <div className="text-center py-8 text-slate-400">
                {type === 'profit' ? 'Kârlı ürün bulunamadı' : 'Zararlı ürün bulunamadı'}
            </div>
        );
    }

    return (
        <div className="overflow-x-auto">
            <table className="w-full">
                <thead>
                    <tr className="text-left text-xs text-slate-500 uppercase border-b border-slate-200">
                        <th className="pb-2">Ürün</th>
                        <th className="pb-2 text-right">{type === 'profit' ? 'Kâr' : 'Zarar'}</th>
                        <th className="pb-2 text-right">Marj</th>
                        <th className="pb-2 text-right">Adet</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                    {products.map((product) => (
                        <tr key={product.barcode} className="text-sm">
                            <td className="py-2">
                                <div className="font-medium text-slate-800 truncate max-w-[150px]">
                                    {product.product_name}
                                </div>
                                <div className="text-xs text-slate-400">{product.barcode}</div>
                            </td>
                            <td
                                className={cn(
                                    'py-2 text-right font-medium',
                                    type === 'profit' ? 'text-success-600' : 'text-danger-500'
                                )}
                            >
                                {formatCurrency(product.total_profit || product.total_loss)}
                            </td>
                            <td
                                className={cn(
                                    'py-2 text-right',
                                    parseFloat(product.avg_margin) >= 0 ? 'text-success-600' : 'text-danger-500'
                                )}
                            >
                                {formatPercent(product.avg_margin)}
                            </td>
                            <td className="py-2 text-right text-slate-600">{product.quantity_sold}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
