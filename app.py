from flask import Flask, render_template, jsonify, request, session, Response
import os
import random
from coordinates import coordinates
from read_the_list import inhabited_islands

app = Flask(__name__)
# On the live site the key comes from the SECRET_KEY environment variable (set it in the hosting dashboard).
# The fallback below is only for running on your own computer.
app.secret_key = os.environ.get('SECRET_KEY', 'local-development-key')

# Override this in Render if your support page changes.
SUPPORT_URL = os.environ.get('SUPPORT_URL', 'https://thx.so/chrisbaf/support')

# Google Search Console HTML-file ownership verification.
@app.route('/google634bedc0b5fefe6d.html')
def google_site_verification():
    return 'google-site-verification: google634bedc0b5fefe6d.html', 200, {'Content-Type': 'text/html; charset=utf-8'}

# Sitemap helps search engines discover the public homepage.
@app.route('/sitemap.xml')
def sitemap():
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://greek-islands-map.onrender.com/</loc>
  </url>
</urlset>'''
    return Response(xml, mimetype='application/xml')

# Allow search engines to crawl the public site and point them to the sitemap.
@app.route('/robots.txt')
def robots_txt():
    content = 'User-agent: *\nAllow: /\nSitemap: https://greek-islands-map.onrender.com/sitemap.xml\n'
    return Response(content, mimetype='text/plain')

greece_center = [39.0742, 21.8243]
all_islands = set(coordinates.keys())

# Island group ("Island complex" column in islands.csv) for every island, plus nicer display names.
REGION_LABELS = {
    'Cyclades': 'Cyclades',
    'Dodecanese': 'Dodecanese',
    'Ionian Islands': 'Ionian Islands',
    'Islands of the north Aegean': 'North Aegean Islands',
    'Argosaronic islands': 'Argosaronic Islands',
    'Northern Sporades': 'Northern Sporades',
    'Islands of Crete': 'Crete',
    'Others': 'Other islands',
}
REGION_ORDER = list(REGION_LABELS.values())

island_region = {}
for row in inhabited_islands:
    group = row['Island complex'].strip()
    island_region[row['Island'] + ', Greece'] = REGION_LABELS.get(group, group)

# Renders the index.html template and clears the session (visited_islands list) to start fresh for each visit.
@app.route('/')
def index():
    session.clear()
    # If someone opens a shared link, restore the islands selected by the sender.
    # Only accept island names that exist in the official coordinates list.
    shared_islands = request.args.getlist('visited')
    session['visited_islands'] = [island for island in shared_islands if island in all_islands]
    return render_template('index.html', support_url=SUPPORT_URL)


# Returns all islands with their coordinates as JSON data from the coordinates dictionary.
@app.route('/islands')
def get_islands():
    return jsonify(coordinates)


@app.route('/visited', methods=['GET'])
def get_visited_islands():
    return jsonify({'visited_islands': session.get('visited_islands', [])})

@app.route('/not_visited', methods=['GET'])
def get_not_visited_islands():
    all_islands = set(coordinates.keys())
    visited_islands = set(session.get('visited_islands', []))
    not_visited_islands = list(all_islands - visited_islands)
    return jsonify({'not_visited_islands': not_visited_islands})

@app.route('/percentage', methods=['GET'])
def get_percentage():
    total_islands = len(coordinates)
    visited_islands = len(session.get('visited_islands', []))
    percentage_visited = (visited_islands / total_islands) * 100
    return jsonify({'percentage_visited': percentage_visited,
                    'visited_count': visited_islands,
                    'total_islands': total_islands})


# Visited / total / percentage for each island group (Cyclades, Dodecanese, ...).
@app.route('/regions', methods=['GET'])
def get_regions():
    visited = set(session.get('visited_islands', []))
    totals, done = {}, {}
    for island in coordinates:
        region = island_region.get(island, 'Other islands')
        totals[region] = totals.get(region, 0) + 1
        if island in visited:
            done[region] = done.get(region, 0) + 1
    ordered = [r for r in REGION_ORDER if r in totals] + [r for r in totals if r not in REGION_ORDER]
    return jsonify({'regions': [
        {'name': r,
         'visited': done.get(r, 0),
         'total': totals[r],
         'percentage': round(done.get(r, 0) / totals[r] * 100, 1)}
        for r in ordered
    ]})

@app.route('/visit', methods=['POST'])
def visit():
    data = request.json
    lat, lon = data['lat'], data['lng']
    for island, coords in coordinates.items():
        if abs(lat - coords[0]) < 0.001 and abs(lon - coords[1]) < 0.001:
            if island not in session.get('visited_islands', []):
                session.setdefault('visited_islands', []).append(island)
                session.modified = True
    visited_count = len(session['visited_islands'])
    total_islands = len(coordinates)
    return jsonify(visited_islands=session['visited_islands'], visited_count=visited_count, total_islands=total_islands)

@app.route('/unvisit', methods=['POST'])
def unvisit():
    data = request.json
    lat, lon = data['lat'], data['lng']
    for island, coords in coordinates.items():
        if abs(lat - coords[0]) < 0.001 and abs(lon - coords[1]) < 0.001:
            if island in session.get('visited_islands', []):
                session['visited_islands'].remove(island)
                session.modified = True
    visited_count = len(session['visited_islands'])
    total_islands = len(coordinates)
    return jsonify(visited_islands=session['visited_islands'], visited_count=visited_count, total_islands=total_islands)

@app.route('/reset', methods=['POST'])
def reset():
    session['visited_islands'] = []
    session.modified = True
    return jsonify({'status': 'reset'})

@app.route('/random_island', methods=['GET'])
def random_island():
    not_visited_islands = list(set(coordinates.keys()) - set(session.get('visited_islands', [])))
    if not_visited_islands:
        random_island = random.choice(not_visited_islands)
        return jsonify({'random_island': random_island})
    return jsonify({'random_island': 'All islands visited'})

if __name__ == '__main__':
    # Only used when you run "python app.py" locally; the live site is started by gunicorn instead.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))