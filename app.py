"""
FB Marketplace 商品監控系統 - Render 部署版
"""
import os
import json
import re
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'products.json')


def load_products():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def compute_stats(products):
    total = len(products)
    underpriced = sum(1 for p in products if p.get('price_verdict') in ('偏低', '略低'))
    overpriced = sum(1 for p in products if p.get('price_verdict') in ('偏高', '略高'))
    fair = sum(1 for p in products if p.get('price_verdict') == '合理')
    avg_listed = sum(p.get('listed_price', 0) for p in products) / total if total else 0
    avg_estimated = sum(p.get('estimated_price', 0) for p in products) / total if total else 0

    by_keyword = {}
    for p in products:
        kw = p.get('keyword', '其他')
        if kw not in by_keyword:
            by_keyword[kw] = {'count': 0, 'total_listed': 0, 'total_estimated': 0}
        by_keyword[kw]['count'] += 1
        by_keyword[kw]['total_listed'] += p.get('listed_price', 0)
        by_keyword[kw]['total_estimated'] += p.get('estimated_price', 0)

    for kw, data in by_keyword.items():
        c = data['count'] or 1
        data['avg_listed'] = round(data['total_listed'] / c)
        data['avg_estimated'] = round(data['total_estimated'] / c)

    by_verdict = {'偏高': 0, '略高': 0, '合理': 0, '略低': 0, '偏低': 0}
    for p in products:
        v = p.get('price_verdict', '無法判斷')
        if v in by_verdict:
            by_verdict[v] += 1

    return {
        'total': total, 'underpriced_count': underpriced,
        'overpriced_count': overpriced, 'fair_count': fair,
        'avg_listed': round(avg_listed), 'avg_estimated': round(avg_estimated),
        'by_keyword': by_keyword, 'by_verdict': by_verdict,
        'timestamp': datetime.now().isoformat(timespec='seconds')
    }


@app.route('/')
def index():
    products = load_products()
    stats = compute_stats(products)
    keywords = sorted(set(p.get('keyword', '') for p in products))
    return render_template('index.html', products=products, stats=stats, keywords=keywords)


@app.route('/api/products')
def api_products():
    products = load_products()
    keyword = request.args.get('keyword', '')
    verdict = request.args.get('verdict', '')
    search = request.args.get('q', '').lower()
    if keyword:
        products = [p for p in products if p.get('keyword') == keyword]
    if verdict:
        products = [p for p in products if p.get('price_verdict') == verdict]
    if search:
        products = [p for p in products if search in p.get('title', '').lower()]
    sort_by = request.args.get('sort', 'diff_asc')
    if sort_by == 'diff_asc':
        products.sort(key=lambda p: p.get('price_diff_pct', 0))
    elif sort_by == 'diff_desc':
        products.sort(key=lambda p: p.get('price_diff_pct', 0), reverse=True)
    elif sort_by == 'price_asc':
        products.sort(key=lambda p: p.get('listed_price', 0))
    elif sort_by == 'price_desc':
        products.sort(key=lambda p: p.get('listed_price', 0), reverse=True)
    elif sort_by == 'score_desc':
        products.sort(key=lambda p: p.get('condition_score', 0), reverse=True)
    return jsonify({'products': products, 'total': len(products)})


@app.route('/api/stats')
def api_stats():
    products = load_products()
    return jsonify(compute_stats(products))


@app.route('/api/export')
def api_export():
    products = load_products()
    header = '關鍵詞,商品名稱,標價,AI估價,差異%,判定,新舊程度,分數,地點,FB連結\n'
    rows = []
    for p in products:
        title = p.get('title', '').replace('"', '""')
        rows.append(f"{p.get('keyword','')},\"{title}\",{p.get('listed_price',0)},{p.get('estimated_price',0)},{p.get('price_diff_pct',0)}%,{p.get('price_verdict','')},{p.get('condition','')},{p.get('condition_score',0)},{p.get('location','')},{p.get('url','')}")
    csv_content = '\ufeff' + header + '\n'.join(rows)
    return Response(csv_content, mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename=marketplace_{datetime.now().strftime("%Y%m%d")}.csv'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
