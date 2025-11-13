import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import time
import os

# ------------------------------
# CẤU HÌNH
# ------------------------------
available_colors = [
    "red", "green", "blue", "yellow", "brown",
    "pink", "orange", "purple", "cyan", "gray"
]

# ------------------------------
# HỖ TRỢ VẼ ĐỒ THỊ TRONG STREAMLIT
# ------------------------------
def draw_graph_streamlit(G, pos, color_assign, title="", highlight_node=None):
    fig, ax = plt.subplots(figsize=(6, 5))
    node_colors = [
        available_colors[color_assign[n]] if color_assign[n] != -1 else "lightgray"
        for n in G.nodes()
    ]
    edgecolors = ["gold" if n == highlight_node else "black" for n in G.nodes()]
    linewidths = [3.0 if n == highlight_node else 1.0 for n in G.nodes()]
    nx.draw_networkx(
        G, pos,
        node_color=node_colors,
        node_size=800,
        edgecolors=edgecolors,
        linewidths=linewidths,
        labels={n: str(n) for n in G.nodes()},
        font_color="white",
        font_weight="bold",
        ax=ax
    )
    plt.title(title)
    plt.axis('off')
    st.pyplot(fig)

# ------------------------------
# HÀM TẠO ĐỒ THỊ
# ------------------------------
def build_graph_from_edges(edges):
    G = nx.Graph()
    G.add_edges_from(edges)
    pos = nx.spring_layout(G, seed=42)
    color_assign = {n: -1 for n in G.nodes()}
    return G, pos, color_assign

# ------------------------------
# HÀM KIỂM TRA AN TOÀN
# ------------------------------
def is_safe(G, color_assign, node, color_index):
    for neighbor in G.neighbors(node):
        if color_assign.get(neighbor, -1) == color_index:
            return False
    return True

# ------------------------------
# BACKTRACKING (hai biến thể: có animation / không)
# ------------------------------
def backtrack_color(G, pos, nodes_list, color_assign, idx, max_colors, draw_func):
    """Phiên bản có animation: gọi draw_func mỗi khi gán/quay lui"""
    if idx == len(nodes_list):
        return True
    node = nodes_list[idx]
    for color_idx in range(max_colors):
        if is_safe(G, color_assign, node, color_idx):
            color_assign[node] = color_idx
            draw_func(G, pos, color_assign, f"Tô đỉnh {node} = {available_colors[color_idx]}", highlight_node=node)
            time.sleep(0.2)
            if backtrack_color(G, pos, nodes_list, color_assign, idx + 1, max_colors, draw_func):
                return True
            color_assign[node] = -1
            draw_func(G, pos, color_assign, f"Quay lui: bỏ màu ở đỉnh {node}", highlight_node=node)
            time.sleep(0.2)
    return False

def backtrack_color_algo(G, color_assign, nodes_list, idx, max_colors):
    """Phiên bản không animation: chỉ thuật toán (dùng để đo time thực)"""
    if idx == len(nodes_list):
        return True
    node = nodes_list[idx]
    for color_idx in range(max_colors):
        if is_safe(G, color_assign, node, color_idx):
            color_assign[node] = color_idx
            if backtrack_color_algo(G, color_assign, nodes_list, idx + 1, max_colors):
                return True
            color_assign[node] = -1
    return False

def run_backtracking(G, pos, nodes_list, color_assign, max_colors, visualize=True):
    """Trả về (ok, elapsed). elapsed là thời gian THUẬT TOÁN (không bao gồm time.sleep/vẽ nếu visualize=False)."""
    if visualize:
        # khi visualize=True, vẫn muốn đo thời gian bao gồm animation? KHÔNG — ta đo thời gian thuật toán nhưng vẽ vẫn diễn ra.
        # Để đo chính xác thời gian thuật toán *không bao gồm* vẽ, ta đo trước và sau khi gọi thuật toán không-visual,
        # nhưng với phiên bản animated cần vẽ từng bước; ở đây ta đo thời gian toàn bộ gọi hàm animated (lưu ý: user muốn đo thuật toán riêng, 
        # nên animation run sẽ hiển thị thời gian animation, mình hiển thị nhãn rõ ràng)
        start = time.time()
        def draw_func(Gg, posg, color_assigng, title, highlight_node=None):
            draw_graph_streamlit(Gg, posg, color_assigng, title, highlight_node)
            time.sleep(0.2)
        ok = backtrack_color(G, pos, nodes_list, color_assign, 0, max_colors, draw_func)
        elapsed = time.time() - start  # thời gian bao gồm vẽ+sleep (dùng cho hiển thị animation)
        return ok, elapsed
    else:
        start = time.time()
        ok = backtrack_color_algo(G, color_assign, nodes_list, 0, max_colors)
        elapsed = time.time() - start  # thời gian THUẬT TOÁN thực tế (không vẽ)
        return ok, elapsed

# ------------------------------
# GREEDY (hai biến thể)
# ------------------------------
def greedy_coloring_algo(G, color_assign, nodes_list, max_colors):
    for node in nodes_list:
        neighbor_colors = {color_assign[nb] for nb in G.neighbors(node) if color_assign[nb] != -1}
        valid_colors = [i for i in range(max_colors) if i not in neighbor_colors]
        if not valid_colors:
            return False
        color_assign[node] = valid_colors[0]
    return True

def greedy_coloring(G, pos, nodes_list, color_assign, max_colors, visualize=True):
    if visualize:
        start = time.time()
        for node in nodes_list:
            neighbor_colors = {color_assign[nb] for nb in G.neighbors(node) if color_assign[nb] != -1}
            valid_colors = [i for i in range(max_colors) if i not in neighbor_colors]
            if not valid_colors:
                elapsed = time.time() - start
                return False, elapsed
            chosen = valid_colors[0]
            color_assign[node] = chosen
            draw_graph_streamlit(G, pos, color_assign, f"Tô đỉnh {node} = {available_colors[chosen]}", highlight_node=node)
            time.sleep(0.2)
        elapsed = time.time() - start  # thời gian bao gồm vẽ+sleep (dùng để hiển thị animation)
        return True, elapsed
    else:
        start = time.time()
        ok = greedy_coloring_algo(G, color_assign, nodes_list, max_colors)
        elapsed = time.time() - start  # thời gian THUẬT TOÁN
        return ok, elapsed

# ------------------------------
# DSATUR (hai biến thể)
# ------------------------------
def dsatur_coloring_algo(G, color_assign, nodes_list, max_colors):
    uncolored = set(nodes_list)
    degrees = {v: G.degree(v) for v in nodes_list}
    while uncolored:
        sat = {v: len({color_assign[n] for n in G.neighbors(v) if color_assign[n] != -1}) for v in uncolored}
        max_sat = max(sat.values())
        candidates = [v for v in uncolored if sat[v] == max_sat]
        node = max(candidates, key=lambda x: degrees[x])
        neighbor_colors = {color_assign[n] for n in G.neighbors(node) if color_assign[n] != -1}
        valid_colors = [i for i in range(max_colors) if i not in neighbor_colors]
        if not valid_colors:
            return False
        color_assign[node] = valid_colors[0]
        uncolored.remove(node)
    return True

def dsatur_coloring(G, pos, nodes_list, color_assign, max_colors, visualize=True):
    if visualize:
        start = time.time()
        uncolored = set(nodes_list)
        degrees = {v: G.degree(v) for v in nodes_list}
        while uncolored:
            sat = {v: len({color_assign[n] for n in G.neighbors(v) if color_assign[n] != -1}) for v in uncolored}
            max_sat = max(sat.values())
            candidates = [v for v in uncolored if sat[v] == max_sat]
            node = max(candidates, key=lambda x: degrees[x])
            neighbor_colors = {color_assign[n] for n in G.neighbors(node) if color_assign[n] != -1}
            valid_colors = [i for i in range(max_colors) if i not in neighbor_colors]
            if not valid_colors:
                elapsed = time.time() - start
                return False, elapsed
            chosen = valid_colors[0]
            color_assign[node] = chosen
            draw_graph_streamlit(G, pos, color_assign, f"Tô đỉnh {node} = {available_colors[chosen]}", highlight_node=node)
            uncolored.remove(node)
            time.sleep(0.2)
        elapsed = time.time() - start  # thời gian bao gồm vẽ+sleep (dùng để hiển thị animation)
        return True, elapsed
    else:
        start = time.time()
        ok = dsatur_coloring_algo(G, color_assign, nodes_list, max_colors)
        elapsed = time.time() - start  # thời gian THUẬT TOÁN
        return ok, elapsed

# ------------------------------
# GIAO DIỆN STREAMLIT
# ------------------------------
st.title("🎨 TRỰC QUAN HÓA THUẬT TOÁN TÔ MÀU ĐỒ THỊ")
st.markdown("Sử dụng **NetworkX + Matplotlib + Streamlit** để mô phỏng quá trình tô màu đỉnh.")

# --- chọn nguồn đồ thị
src = st.radio("Nguồn đồ thị:", ["Mặc định", "Nhập thủ công", "Đọc từ file data.txt"])
edges = []

if src == "Nhập thủ công":
    st.info("Nhập mỗi cạnh dạng `u v` (vd: 1 2), mỗi dòng một cạnh.")
    text = st.text_area("Nhập cạnh:")
    for line in text.strip().splitlines():
        parts = line.split()
        if len(parts) == 2:
            try:
                u, v = int(parts[0]), int(parts[1])
                edges.append((u, v))
            except:
                pass
elif src == "Đọc từ file data.txt":
    if os.path.exists("data.txt"):
        with open("data.txt") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    try:
                        u, v = int(parts[0]), int(parts[1])
                        edges.append((u, v))
                    except:
                        pass
    else:
        st.error("Không tìm thấy file data.txt trong thư mục hiện tại.")
else:
    edges = [
        (1, 2), (1, 3), (3, 4), (2, 6),
        (3, 5), (1, 6), (1, 5), (4, 5), (5, 6)
    ]

if edges:
    G, pos, color_assign = build_graph_from_edges(edges)
    nodes_list = sorted(G.nodes())
    draw_graph_streamlit(G, pos, color_assign, "Đồ thị ban đầu")

    algo_choice = st.selectbox("Chọn thuật toán:", ["Backtracking", "Greedy", "DSATUR"])
    num_colors = st.slider("Số lượng màu:", 1, len(available_colors), 4)
    start_btn = st.button("🚀 Bắt đầu tô màu (với animation)")

    if start_btn:
        # reset màu trước khi chạy animation
        for n in nodes_list:
            color_assign[n] = -1

        if algo_choice == "Backtracking":
            ok, elapsed = run_backtracking(G, pos, nodes_list, color_assign, num_colors, visualize=True)
        elif algo_choice == "Greedy":
            ok, elapsed = greedy_coloring(G, pos, nodes_list, color_assign, num_colors, visualize=True)
        else:
            ok, elapsed = dsatur_coloring(G, pos, nodes_list, color_assign, num_colors, visualize=True)

        if ok:
            st.success(f"✅ Hoàn tất tô màu (animation). Thời gian hiển thị (bao gồm vẽ/animation): {elapsed:.3f} s.")
        else:
            st.error(f"❌ Không thể tô hợp lệ với {num_colors} màu (thời gian hiển thị {elapsed:.3f}s).")

    # ----------------------
    # 🔍 TÌM SỐ MÀU TỐI ƯU (tính tổng thời gian thuật toán khi thử các k)
    # ----------------------
    st.markdown("---")
    st.markdown("Tìm số màu tối ưu (chỉ tính **thời gian thực của thuật toán** trong quá trình thử các k, không tính animation).")
    show_final_anim = st.checkbox("Hiển thị animation cho kết quả cuối (nếu tìm thấy)", value=False)
    find_opt_btn = st.button("🔍 Tìm số lượng màu tối ưu")

    if find_opt_btn:
        st.info("Đang thử các giá trị k từ nhỏ đến lớn... (tính tổng thời gian thuật toán của tất cả lần thử)")
        optimal = None
        total_elapsed = 0.0
        details = []
        for k in range(1, len(available_colors) + 1):
            # reset màu
            for n in nodes_list:
                color_assign[n] = -1

            if algo_choice == "Backtracking":
                ok, elapsed = run_backtracking(G, pos, nodes_list, color_assign, k, visualize=False)
            elif algo_choice == "Greedy":
                ok, elapsed = greedy_coloring(G, pos, nodes_list, color_assign, k, visualize=False)
            else:
                ok, elapsed = dsatur_coloring(G, pos, nodes_list, color_assign, k, visualize=False)

            total_elapsed += elapsed
            details.append((k, ok, elapsed))

            if ok:
                optimal = k
                st.success(f"✅ Thử k={k}: TÔ HỢP LỆ (thời gian thuật toán lần này: {elapsed:.6f} s).")
                break
            else:
                st.write(f"❌ Thử k={k}: KHÔNG HỢP LỆ (thời gian thuật toán lần này: {elapsed:.6f} s).")

        # Hiển thị tóm tắt
        st.markdown("---")
        st.write("Chi tiết mỗi lần thử (k, hợp lệ?, thời gian thuật toán):")
        for k, ok, elapsed in details:
            st.write(f"- k={k}: {'OK' if ok else 'NO'} — {elapsed:.6f} s")

        st.write(f"⏱️ Tổng thời gian thuật toán đã tốn khi tìm: **{total_elapsed:.6f} s**")

        if optimal:
            st.success(f"🎯 **Số màu tối ưu (theo thuật toán {algo_choice}) = {optimal}**")
            # Nếu user muốn, hiển thị animation cho kết quả cuối
            if show_final_anim:
                # reset màu rồi chạy lại với visualize=True để vẽ animation kết quả
                for n in nodes_list:
                    color_assign[n] = -1
                st.info(f"Hiển thị animation cho k={optimal} ...")
                if algo_choice == "Backtracking":
                    ok2, elapsed2 = run_backtracking(G, pos, nodes_list, color_assign, optimal, visualize=True)
                elif algo_choice == "Greedy":
                    ok2, elapsed2 = greedy_coloring(G, pos, nodes_list, color_assign, optimal, visualize=True)
                else:
                    ok2, elapsed2 = dsatur_coloring(G, pos, nodes_list, color_assign, optimal, visualize=True)
                if ok2:
                    st.success(f"✅ Animation hoàn tất (thời gian hiển thị: {elapsed2:.3f} s).")
                else:
                    st.error("⚠️ Kỳ lạ — khi chạy animation cho k tối ưu lại không hợp lệ (cần kiểm tra).")
        else:
            st.error("❌ Không tìm thấy k hợp lệ trong phạm vi màu cho phép.")
else:
    st.warning("⚠️ Chưa có cạnh hợp lệ để tạo đồ thị.")
