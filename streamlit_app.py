import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import time
from collections import Counter
import sys
import os
# ------------------------------
# CẤU HÌNH BAN ĐẦU / HÀM HỖ TRỢ
# ------------------------------
# Cài đặt Matplotlib
plt.rcParams['figure.figsize'] = [5, 4]
# Màu mặc định
available_colors_list = ["red", "green", "blue", "yellow", "brown", "pink", "orange", "purple", "cyan", "gray"]
MAX_DEFAULT_COLORS = len(available_colors_list)
# Khởi tạo hoặc truy cập Session State
if 'algo_accum' not in st.session_state:
    st.session_state.algo_accum = 0.0
if 'algo_start' not in st.session_state:
    st.session_state.algo_start = None
if 'available_colors' not in st.session_state:
    st.session_state.available_colors = list(available_colors_list)
# Hàm quản lý Timer
def algo_reset():
    st.session_state.algo_start = None
    st.session_state.algo_accum = 0.0
def algo_start_timer():
    if st.session_state.algo_start is None:
        st.session_state.algo_start = time.time()
def algo_pause_timer_for_draw():
    if st.session_state.algo_start is not None:
        st.session_state.algo_accum += time.time() - st.session_state.algo_start
        st.session_state.algo_start = None
def algo_resume_timer_after_draw():
    if st.session_state.algo_start is None:
        st.session_state.algo_start = time.time()
def algo_stop_timer():
    if st.session_state.algo_start is not None:
        st.session_state.algo_accum += time.time() - st.session_state.algo_start
        st.session_state.algo_start = None
    return st.session_state.algo_accum
# Hàm busy sleep để thay thế time.sleep trong Pyodide
def busy_sleep(delay):
    if delay > 0:
        start = time.time()
        while time.time() - start < delay:
            pass
# ------------------------------
# HÀM XÂY DỰNG / ĐỌC ĐỒ THỊ
# ------------------------------
def build_graph_from_edges(edges):
    """Trả về G,pos,nodes_list,color_assign khởi tạo"""
    G = nx.Graph()
    G.add_edges_from(edges)
   
    # Thêm các đỉnh bị cô lập
    all_nodes = set()
    for u, v in edges:
        all_nodes.add(u)
        all_nodes.add(v)
    # Tìm các đỉnh cô lập trong input (cạnh giả (n, n) đã bị loại bỏ)
    if len(G.nodes()) != len(all_nodes):
        G.add_nodes_from(all_nodes)
   
    if len(G.nodes()) == 0:
        return None, None, [], {}
       
    pos = nx.spring_layout(G, seed=42)
    nodes_list = sorted(G.nodes())
    color_assign = {n: -1 for n in nodes_list}
    return G, pos, nodes_list, color_assign
def parse_input_edges(input_text):
    edges = []
    for line in input_text.split('\n'):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) >= 2:
            try:
                u = int(parts[0])
                v = int(parts[1])
                if u != v: # Bỏ qua cạnh lặp (self-loop)
                    edges.append(tuple(sorted((u, v))))
            except ValueError:
                st.warning(f"Bỏ qua dòng không hợp lệ: {line}")
        elif len(parts) == 1:
            try:
                node = int(parts[0])
                # Để Streamlit có thể thêm đỉnh cô lập, ta thêm một cạnh lặp giả
                edges.append((node, node))
            except ValueError:
                st.warning(f"Bỏ qua đỉnh cô lập không hợp lệ: {line}")
               
    return list(set(edges))
# ------------------------------
# KHỞI TẠO MẶC ĐỊNH
# ------------------------------
default_edges_text = """
1 2
1 3
3 4
2 6
3 5
1 6
1 5
4 5
5 6

# ------------------------------
# HÀM VẼ CHUNG (Đã tích hợp st.status)
# ------------------------------
def draw_graph_step(G, pos, nodes_list, color_assign, highlight_node=None, title="", delay=0.0, status_context=None):
    fig, ax = plt.subplots()
   
    current_colors = st.session_state.available_colors
   
    node_colors = [
        current_colors[color_assign[n]] if color_assign.get(n, -1) != -1 else "lightgray"
        for n in nodes_list
    ]
    edgecolors = ["gold" if n == highlight_node else "black" for n in nodes_list]
    linewidths = [3.0 if n == highlight_node else 1.0 for n in nodes_list]
    nx.draw_networkx_nodes(
        G, pos,
        nodelist=nodes_list,
        node_color=node_colors,
        node_size=600,
        edgecolors=edgecolors,
        linewidths=linewidths,
        ax=ax
    )
    nx.draw_networkx_labels(G, pos, labels={n: str(n) for n in nodes_list},
                            font_size=10, font_weight="bold", font_color="white", ax=ax)
    nx.draw_networkx_edges(G, pos, ax=ax)
    ax.set_title(title, fontsize=10)
    ax.axis('off')
    # Hiển thị đồ thị
    st.session_state.fig_placeholder.pyplot(fig, use_container_width=False)
    plt.close(fig)
   
    # Cập nhật trạng thái trong st.status (nếu có)
    if status_context:
        status_context.update(label=title, state="running", expanded=True)
    # Tạm dừng timer trước animation
    algo_pause_timer_for_draw()
    if delay > 0:
        busy_sleep(delay)
    algo_resume_timer_after_draw()
# ------------------------------
# FIND_MIN COLORS (Đã tích hợp st.status)
# ------------------------------
def find_min_colors(algorithm_func, G, pos, nodes_list, color_assign_ref, initial_max, algo_name, delay_time):
   
    initial_max_color_index = initial_max
    total_algo_time = 0.0
    found_k = None
   
    # Sử dụng st.status để quản lý toàn bộ tiến trình
    with st.status(f"Đang tìm số màu tối ưu bằng {algo_name}...", expanded=True) as status:
       
        for k in range(1, initial_max_color_index + 1):
           
            # Sử dụng st.progress bên trong st.status để hiển thị tiến trình thử màu
            status.progress(k / initial_max_color_index, text=f"Đang thử với {k} màu...")
           
            # reset màu
            for n in nodes_list:
                color_assign_ref[n] = -1
            st.session_state.available_colors = list(available_colors_list)
            draw_graph_step(G, pos, nodes_list, color_assign_ref,
                            title=f"Đang thử với {k} màu...", delay=delay_time, status_context=status)
            # Chạy thuật toán (ĐẢM BẢO HÀM ĐỒNG BỘ DEF)
            ok, elapsed_algo = algorithm_func(G, pos, nodes_list, color_assign_ref, k,
                                            keep_open=True, show_time=False, allow_expand=False,
                                            delay_time=delay_time, status_context=status) # Truyền context
            total_algo_time += elapsed_algo
            if ok:
                found_k = k
                break
            else:
                draw_graph_step(G, pos, nodes_list, color_assign_ref,
                                title=f"Thử {k} màu thất bại — chuyển sang {k + 1} màu...", delay=delay_time, status_context=status)
        if found_k is not None:
            final_title = f"✅ Tìm được số màu tối ưu: {found_k} | T.gian thuật toán: {total_algo_time:.3f}s"
            status.update(label=final_title, state="complete", expanded=False)
            draw_graph_step(G, pos, nodes_list, color_assign_ref, title=final_title.replace("|", "\n"), delay=0.0)
            st.sidebar.info(f"Số màu tối ưu (χ(G)): **{found_k}**")
            return found_k
        else:
            final_title = f"❌ Không tìm được số màu trong phạm vi {initial_max_color_index} màu | T.gian thuật toán: {total_algo_time:.3f}s"
            status.update(label=final_title, state="error", expanded=True)
            draw_graph_step(G, pos, nodes_list, color_assign_ref, title=final_title.replace("|", "\n"), delay=0.0)
            st.sidebar.error(f"Không tìm thấy kết quả trong giới hạn {initial_max_color_index} màu.")
            return None
# ------------------------------
# CÁC THUẬT TOÁN VÀ HÀM CHẠY (Đảm bảo là DEF và có tham số status_context)
# ------------------------------
def run_algorithm(G, pos, nodes_list, color_assign_ref, algorithm_choice, color_mode, num_colors, delay_time):
   
    # --- BACKTRACKING ---
    def is_safe(node, color_index):
        for neighbor in G.neighbors(node):
            if color_assign_ref.get(neighbor, -1) == color_index:
                return False
        return True
    def backtrack_color(idx, max_colors, allow_expand, status_context):
        if idx == len(nodes_list):
            return True
        node = nodes_list[idx]
        max_try = len(st.session_state.available_colors) if allow_expand else max_colors
        for color_idx in range(max_try):
            is_new_color_slot = color_idx >= len(st.session_state.available_colors)
            if is_new_color_slot:
                if allow_expand:
                    new_color = f"C{len(st.session_state.available_colors)}"
                    st.session_state.available_colors.append(new_color)
                else:
                    break
           
            if is_safe(node, color_idx):
                color_assign_ref[node] = color_idx
                cname = st.session_state.available_colors[color_idx]
                draw_graph_step(G, pos, nodes_list, color_assign_ref, highlight_node=node,
                                title=f"[BT] Tô đỉnh {node} = {cname}", delay=delay_time, status_context=status_context)
               
                if backtrack_color(idx + 1, max_colors, allow_expand, status_context):
                    return True
               
                color_assign_ref[node] = -1
                draw_graph_step(G, pos, nodes_list, color_assign_ref, highlight_node=node,
                                title=f"[BT] Quay lui: bỏ màu ở đỉnh {node}", delay=delay_time * 1.5, status_context=status_context)
        return False
    def run_backtracking(G, pos, nodes_list, color_assign_ref, max_colors, keep_open, show_time, allow_expand, delay_time, status_context=None):
       
        if status_context: status_context.write(f"Đang chạy Backtracking (Max Màu: {max_colors if not allow_expand else '∞'})")
        draw_graph_step(G, pos, nodes_list, color_assign_ref, title=f"Bắt đầu tô màu (Backtracking) - đang thử {max_colors} màu", delay=delay_time, status_context=status_context)
        algo_reset()
        algo_start_timer()
        ok = backtrack_color(0, max_colors, allow_expand, status_context)
        elapsed_algo = algo_stop_timer()
        if show_time:
            if ok:
                final_title = f"Tô hoàn tất\n T.gian: {elapsed_algo:.3f}s"
            else:
                final_title = f"Tô không thành công\n T.gian: {elapsed_algo:.3f}s"
            if status_context: status_context.write(final_title)
            draw_graph_step(G, pos, nodes_list, color_assign_ref, title=final_title.replace("\n", "\n"), delay=0.0, status_context=status_context)
        return ok, elapsed_algo
    # --- GREEDY ---
    def greedy_coloring(G, pos, nodes_list, color_assign_ref, max_colors, keep_open, show_time, allow_expand, delay_time, status_context=None):
       
        if status_context: status_context.write(f"Đang chạy Greedy (Max Màu: {max_colors if not allow_expand else '∞'})")
        draw_graph_step(G, pos, nodes_list, color_assign_ref, title=f"Bắt đầu tô màu (Greedy) - đang thử {max_colors} màu", delay=delay_time, status_context=status_context)
        algo_reset()
        algo_start_timer()
        for node in nodes_list:
            draw_graph_step(G, pos, nodes_list, color_assign_ref, highlight_node=node, title=f"[G] Đang tô đỉnh {node}...", delay=delay_time, status_context=status_context)
            neighbor_colors = {color_assign_ref[nb] for nb in G.neighbors(node) if color_assign_ref.get(nb, -1) != -1}
            current_color_limit = len(st.session_state.available_colors) if allow_expand else max_colors
           
            valid_colors = [i for i in range(current_color_limit) if i not in neighbor_colors]
            chosen = None
           
            if valid_colors:
                chosen = valid_colors[0]
            elif allow_expand:
                new_color_idx = len(st.session_state.available_colors)
                new_color = f"C{new_color_idx}"
                st.session_state.available_colors.append(new_color)
                if status_context: status_context.write(f"Thêm màu mới (Greedy): {new_color}")
                chosen = new_color_idx
            if chosen is not None:
                color_assign_ref[node] = chosen
                cname = st.session_state.available_colors[chosen]
                draw_graph_step(G, pos, nodes_list, color_assign_ref, highlight_node=node, title=f"[G] Tô đỉnh {node} = {cname}", delay=delay_time, status_context=status_context)
            else:
                elapsed_algo = algo_stop_timer()
                final_title = f"Tô không thành công\n T.gian: {elapsed_algo:.3f}s"
                if status_context: status_context.write(final_title)
                draw_graph_step(G, pos, nodes_list, color_assign_ref, highlight_node=node, title=final_title.replace("\n", "\n"), delay=0.0, status_context=status_context)
                return False, elapsed_algo
        elapsed_algo = algo_stop_timer()
        final_title = f"Tô hoàn tất\n T.gian: {elapsed_algo:.3f}s"
        if status_context: status_context.write(final_title)
        draw_graph_step(G, pos, nodes_list, color_assign_ref, title=final_title.replace("\n", "\n"), delay=0.0, status_context=status_context)
        return True, elapsed_algo
    # --- DSATUR ---
    def dsatur_coloring(G, pos, nodes_list, color_assign_ref, max_colors, keep_open, show_time, allow_expand, delay_time, status_context=None):
       
        if status_context: status_context.write(f"Đang chạy DSATUR (Max Màu: {max_colors if not allow_expand else '∞'})")
        draw_graph_step(G, pos, nodes_list, color_assign_ref, title=f"Bắt đầu tô màu (DSATUR) - đang thử {max_colors} màu", delay=delay_time, status_context=status_context)
        algo_reset()
        algo_start_timer()
        uncolored = set(nodes_list)
        degrees = {v: G.degree(v) for v in nodes_list}
        while uncolored:
            # 1. Tính độ bão hòa (Saturation Degree - SAT)
            sat = {}
            for v in uncolored:
                sat[v] = len({color_assign_ref[n] for n in G.neighbors(v) if color_assign_ref.get(n, -1) != -1})
            # 2. Chọn đỉnh (ưu tiên MAX SAT, sau đó MAX Degree)
            max_sat = max(sat.values())
            candidates = [v for v in uncolored if sat[v] == max_sat]
            if len(candidates) > 1:
                node = max(candidates, key=lambda x: degrees[x])
            else:
                node = candidates[0]
           
            draw_graph_step(G, pos, nodes_list, color_assign_ref, highlight_node=node,
                            title=f"[DSATUR] Tô đỉnh {node} (SAT={max_sat})...", delay=delay_time, status_context=status_context)
            # 3. Tô màu
            neighbor_colors = {color_assign_ref[n] for n in G.neighbors(node) if color_assign_ref.get(n, -1) != -1}
            current_color_limit = len(st.session_state.available_colors) if allow_expand else max_colors
           
            valid_colors = [i for i in range(current_color_limit) if i not in neighbor_colors]
            chosen = None
            if valid_colors:
                chosen = valid_colors[0]
            elif allow_expand:
                new_color_idx = len(st.session_state.available_colors)
                new_color = f"C{new_color_idx}"
                st.session_state.available_colors.append(new_color)
                if status_context: status_context.write(f"Thêm màu mới (DSATUR): {new_color}")
                chosen = new_color_idx
           
            if chosen is not None:
                color_assign_ref[node] = chosen
                cname = st.session_state.available_colors[chosen]
                draw_graph_step(G, pos, nodes_list, color_assign_ref, highlight_node=node,
                                title=f"[DSATUR] Tô đỉnh {node} = {cname}", delay=delay_time, status_context=status_context)
            else:
                elapsed_algo = algo_stop_timer()
                final_title = f"Tô không thành công\n T.gian: {elapsed_algo:.3f}s"
                if status_context: status_context.write(final_title)
                draw_graph_step(G, pos, nodes_list, color_assign_ref, highlight_node=node, title=final_title.replace("\n", "\n"), delay=0.0, status_context=status_context)
                return False, elapsed_algo
            uncolored.remove(node)
        elapsed_algo = algo_stop_timer()
        final_title = f"Tô hoàn tất\n T.gian: {elapsed_algo:.3f}s"
        if status_context: status_context.write(final_title)
        draw_graph_step(G, pos, nodes_list, color_assign_ref, title=final_title.replace("\n", "\n"), delay=0.0, status_context=status_context)
        return True, elapsed_algo
   
    # Ánh xạ
    if algorithm_choice == "Backtracking":
        algo_func = run_backtracking
    elif algorithm_choice == "Greedy":
        algo_func = greedy_coloring
    elif algorithm_choice == "DSatur":
        algo_func = dsatur_coloring
    else:
        st.error("Lựa chọn thuật toán không hợp lệ.")
        return
    # Chạy theo chế độ màu
    if color_mode == "Chạy với X màu cố định":
        if num_colors <= 0:
            st.warning("Số lượng màu phải lớn hơn 0.")
            return
       
        for n in nodes_list:
            color_assign_ref[n] = -1
        st.session_state.available_colors = list(available_colors_list)
        # Sử dụng st.status cho chế độ này
        with st.status(f"Đang chạy {algorithm_choice} với {num_colors} màu...", expanded=True) as status:
            ok, elapsed = algo_func(G, pos, nodes_list, color_assign_ref, num_colors, keep_open=False, show_time=True, allow_expand=False, delay_time=delay_time, status_context=status)
           
            if ok:
                used_colors = len(set(color_assign_ref.values()) - {-1})
                status.update(label=f"✅ Tô màu thành công: {used_colors} màu!", state="complete", expanded=False)
                st.sidebar.success(f"Tô màu thành công với **{used_colors}** màu.")
            else:
                status.update(label="❌ Tô màu thất bại.", state="error", expanded=True)
                st.sidebar.error("Tô màu thất bại (hết số màu cho phép).")
    elif color_mode == "Tự tìm số lượng màu tối ưu":
        find_min_colors(algo_func, G, pos, nodes_list, color_assign_ref, initial_max=MAX_DEFAULT_COLORS, algo_name=algorithm_choice, delay_time=delay_time)
# ------------------------------
# GIAO DIỆN STREAMLIT
# ------------------------------
st.set_page_config(page_title="Graph Coloring Visualization", layout="wide")
st.title("🎨 Mô phỏng Thuật toán Tô màu Đồ thị (Graph Coloring)")
st.caption("Ứng dụng mô phỏng các thuật toán Backtracking, Greedy và DSATUR với animation trực quan.")
# Khởi tạo trạng thái phiên (session state)
if 'G' not in st.session_state or 'edges_text' not in st.session_state:
    st.session_state.edges_text = default_edges_text
    edges = parse_input_edges(default_edges_text)
    st.session_state.G, st.session_state.pos, st.session_state.nodes_list, st.session_state.color_assign = build_graph_from_edges(edges)
    st.session_state.available_colors = list(available_colors_list)
# Hàm reset khi thay đổi thuật toán
def reset_on_algo_change():
    if 'nodes_list' in st.session_state:
        st.session_state.color_assign = {n: -1 for n in st.session_state.nodes_list}
        st.session_state.available_colors = list(available_colors_list)
# ------------------------------
# SIDEBAR: Cấu hình đồ thị và thuật toán
# ------------------------------
with st.sidebar:
    st.header("⚙️ Cấu hình")
   
    st.subheader("1. Dữ liệu Đồ thị")
    new_edges_text = st.text_area(
        "Nhập các cạnh (mẫu: 'u v', mỗi dòng một cạnh, hoặc chỉ đỉnh cô lập)",
        st.session_state.edges_text, height=180
    )
   
    if new_edges_text != st.session_state.edges_text:
        st.session_state.edges_text = new_edges_text
        edges = parse_input_edges(new_edges_text)
        G, pos, nodes_list, color_assign = build_graph_from_edges(edges)
        if G:
            st.session_state.G = G
            st.session_state.pos = pos
            st.session_state.nodes_list = nodes_list
            st.session_state.color_assign = color_assign
            st.session_state.available_colors = list(available_colors_list)
            st.rerun()
    st.markdown("---")
    st.subheader("2. Cấu hình Thuật toán")
   
    algorithm_choice = st.selectbox(
        "Chọn Thuật toán",
        ("Backtracking", "Greedy", "DSatur"),
        on_change=reset_on_algo_change
    )
   
    color_mode = st.radio(
        "Chọn Chế độ Màu",
        ("Chạy với X màu cố định", "Tự tìm số lượng màu tối ưu"),
        index=1
    )
   
    num_colors = None
    if color_mode == "Chạy với X màu cố định":
        num_colors = st.number_input(
            f"Nhập số lượng màu (Max cho phép: {MAX_DEFAULT_COLORS}):",
            min_value=1, value=4, max_value=MAX_DEFAULT_COLORS
        )
       
    delay_time = st.slider("Tốc độ Animation (giây/bước)", min_value=0.0, max_value=1.5, value=0.5, step=0.1)
   
    st.markdown("---")
    if st.button("▶️ **BẮT ĐẦU TÔ MÀU**", use_container_width=True, type="primary"):
        st.session_state.run_algo = True
    else:
        if 'run_algo' not in st.session_state:
             st.session_state.run_algo = False
# ------------------------------
# MAIN CONTENT: Hiển thị đồ thị
# ------------------------------
st.markdown("## Kết quả Mô phỏng")
st.session_state.fig_placeholder = st.empty()
if st.session_state.G and len(st.session_state.G.nodes()) > 0:
    draw_graph_step(
        st.session_state.G,
        st.session_state.pos,
        st.session_state.nodes_list,
        st.session_state.color_assign,
        title="Đồ thị đã tải (Chưa tô màu)",
        delay=0.0
    )
else:
    st.warning("⚠️ Vui lòng nhập dữ liệu đồ thị hợp lệ.")
if st.session_state.get('run_algo', False):
   
    if st.session_state.G and len(st.session_state.G.nodes()) > 0:
        st.session_state.color_assign = {n: -1 for n in st.session_state.nodes_list}
        st.session_state.available_colors = list(available_colors_list)
        run_algorithm(
            st.session_state.G,
            st.session_state.pos,
            st.session_state.nodes_list,
            st.session_state.color_assign,
            algorithm_choice,
            color_mode,
            num_colors,
            delay_time
        )
    else:
        st.error("Không thể chạy thuật toán vì đồ thị rỗng hoặc không hợp lệ.")
    st.session_state.run_algo = False
# ------------------------------
# THÔNG TIN THÊM VÀ KẾT QUẢ
# ------------------------------
st.markdown("---")
if st.session_state.G and len(st.session_state.G.nodes()) > 0:
   
    used_colors_final = len(set(st.session_state.color_assign.values()) - {-1})
   
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Thông tin Đồ thị")
        st.metric("Số đỉnh (Vertices)", len(st.session_state.G.nodes()))
        st.metric("Số cạnh (Edges)", len(st.session_state.G.edges()))
       
    with col2:
        st.subheader("💡 Kết quả Cuối cùng")
        if used_colors_final > 0:
             st.metric("Số màu đã sử dụng (χ)", used_colors_final)
        else:
            st.info("Chưa chạy thuật toán hoặc đồ thị rỗng.")
       
        st.markdown("**Chú thích Màu sắc:**")
        color_data = []
        for i, color_name in enumerate(st.session_state.available_colors):
            if i < used_colors_final:
                color_data.append(f"Màu **{i+1}** ({color_name})")
       
        if color_data:
            st.markdown(", ".join(color_data))
        else:
            st.caption("Chưa có màu nào được tô.")
