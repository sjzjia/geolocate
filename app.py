from flask import Flask, request, jsonify, render_template
import maxminddb
import os
import socket

app = Flask(__name__)

# GeoLite2-City.mmdb 的路径
CITY_DB_PATH = 'GeoLite2-City.mmdb'
# GeoLite2-ASN.mmdb 的路径
ASN_DB_PATH = 'GeoLite2-ASN.mmdb'

# 检查 City 数据库是否存在
if not os.path.exists(CITY_DB_PATH):
    print(f"错误：'{CITY_DB_PATH}' 文件未找到。请确保它在正确的路径下。")
    print("你可以从 MaxMind 网站下载 GeoLite2-City.mmdb 文件。")
    exit()

# 检查 ASN 数据库是否存在
if not os.path.exists(ASN_DB_PATH):
    print(f"错误：'{ASN_DB_PATH}' 文件未找到。请确保它在正确的路径下。")
    print("你可以从 MaxMind 网站下载 GeoLite2-ASN.mmdb 文件。")
    exit()

try:
    # 打开 City 数据库
    city_reader = maxminddb.open_database(CITY_DB_PATH)
except maxminddb.InvalidDatabaseError:
    print(f"错误：'{CITY_DB_PATH}' 不是一个有效的 MaxMind DB 数据库文件。")
    exit()
except Exception as e:
    print(f"打开 City 数据库时发生错误：{e}")
    exit()

try:
    # 打开 ASN 数据库
    asn_reader = maxminddb.open_database(ASN_DB_PATH)
except maxminddb.InvalidDatabaseError:
    print(f"错误：'{ASN_DB_PATH}' 不是一个有效的 MaxMind DB 数据库文件。")
    exit()
except Exception as e:
    print(f"打开 ASN 数据库时发生错误：{e}")
    exit()

@app.route('/')
def index():
    """
    渲染主页模板。
    """
    return render_template('index.html')

@app.route('/lookup_detailed', methods=['GET', 'POST'])
def lookup_detailed():
    """
    根据请求的 IP 地址或域名查询详细的地理位置和 ASN 信息。
    """
    query_input = None
    if request.method == 'POST':
        query_input = request.json.get('query')
    elif request.method == 'GET':
        query_input = request.args.get('query')

    # 如果没有提供查询输入，则尝试获取客户端 IP 地址
    if not query_input:
        # 优先使用 X-Forwarded-For 头部（处理代理或负载均衡器）
        if 'X-Forwarded-For' in request.headers:
            ip_address_to_lookup = request.headers['X-Forwarded-For'].split(',')[0].strip()
        else:
            # 否则使用 remote_addr
            ip_address_to_lookup = request.remote_addr
    else:
        ip_address_to_lookup = query_input

    if not ip_address_to_lookup:
        return jsonify({"error": "No IP address or domain provided."}), 400

    original_query = ip_address_to_lookup # 记录原始查询，可能是域名

    # 如果输入不是有效的 IP 地址，尝试解析为 IP 地址
    if not is_valid_ip(ip_address_to_lookup):
        try:
            ip_address_to_lookup = socket.gethostbyname(ip_address_to_lookup)
        except socket.gaierror:
            return jsonify({"error": f"Invalid domain or IP address: '{original_query}'"}), 400
        except Exception as e:
            return jsonify({"error": f"Failed to resolve domain '{original_query}': {str(e)}"}), 500

    try:
        # 查询 City 数据库
        city_response = city_reader.get(ip_address_to_lookup)
        # 查询 ASN 数据库
        asn_response = asn_reader.get(ip_address_to_lookup)

        # 提取 City 信息
        country_name_en = city_response.get('country', {}).get('names', {}).get('en', 'Not Found') if city_response else 'Not Found'
        iso_code = city_response.get('country', {}).get('iso_code', 'N/A') if city_response else 'N/A'
        city_name_en = city_response.get('city', {}).get('names', {}).get('en', 'N/A') if city_response else 'N/A'
        # 获取州/省/区域信息
        subdivisions = city_response.get('subdivisions', []) if city_response else []
        subdivision_name_en = subdivisions[0].get('names', {}).get('en', 'N/A') if subdivisions else 'N/A'
        postal_code = city_response.get('postal', {}).get('code', 'N/A') if city_response else 'N/A'
        latitude = city_response.get('location', {}).get('latitude', 'N/A') if city_response else 'N/A'
        longitude = city_response.get('location', {}).get('longitude', 'N/A') if city_response else 'N/A'

        # 提取 ASN 信息
        asn = asn_response.get('autonomous_system_number', 'N/A') if asn_response else 'N/A'
        asn_organization = asn_response.get('autonomous_system_organization', 'N/A') if asn_response else 'N/A'

        return jsonify({
            "query_input": original_query,
            "resolved_ip": ip_address_to_lookup,
            "country_name": country_name_en,
            "iso_code": iso_code,
            "city_name": city_name_en,
            "subdivision_name": subdivision_name_en,
            "postal_code": postal_code,
            "latitude": latitude,
            "longitude": longitude,
            "asn": asn,
            "asn_organization": asn_organization
        })

    except Exception as e:
        # 捕获其他未知错误
        return jsonify({"error": f"An error occurred during lookup: {str(e)}"}), 500

def is_valid_ip(ip_str):
    """
    检查给定字符串是否为有效的 IPv4 地址。
    """
    try:
        socket.inet_aton(ip_str)
        return True
    except socket.error:
        return False

if __name__ == '__main__':
    # 如果 'templates' 文件夹不存在，则创建它
    if not os.path.exists('templates'):
        os.makedirs('templates')
    # 运行 Flask 应用，开发模式下启用 debug，监听所有接口，端口 80
    app.run(debug=True, host='0.0.0.0', port=80)
