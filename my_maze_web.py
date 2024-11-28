import random
from PIL import Image, ImageDraw
from simpleai.search import SearchProblem, astar
import streamlit as st
from streamlit_drawable_canvas import st_canvas

# Định nghĩa bản đồ
MAP = """
##############################
#    #     #          #      #
## # ##### ###   #####   #####
#  # #         #       #     #
#  # #######   ####### #######
#  #               #         #
#  ####### # ####  # #########
#          #    #  #         #
##############################
"""

# Chuyển đổi bản đồ thành danh sách
MAP = [list(x) for x in MAP.split("\n") if x]

# Đọc ảnh maze.bmp
maze_image_path = "./maze.bmp"  # Đảm bảo rằng file maze.bmp tồn tại trong thư mục
bg_image = Image.open(maze_image_path)

# Thu nhỏ ảnh xuống một tỷ lệ
SCALE_FACTOR = 0.58888
IMAGE_WIDTH, IMAGE_HEIGHT = int(bg_image.width * SCALE_FACTOR), int(bg_image.height * SCALE_FACTOR)
bg_image = bg_image.resize((IMAGE_WIDTH, IMAGE_HEIGHT))

# Kiểm tra MAP để tránh lỗi
if len(MAP) == 0 or len(MAP[0]) == 0:
    st.error("MAP không hợp lệ!")
    st.stop()

# Tính toán kích thước ô sau khi thu nhỏ
CELL_WIDTH = IMAGE_WIDTH // len(MAP[0]) if len(MAP[0]) > 0 else None
CELL_HEIGHT = IMAGE_HEIGHT // len(MAP) if len(MAP) > 0 else None

# Đảm bảo CELL_WIDTH và CELL_HEIGHT không phải là None
if CELL_WIDTH is None or CELL_HEIGHT is None:
    st.error("CELL_WIDTH hoặc CELL_HEIGHT không được khởi tạo!")
    st.stop()

# Định nghĩa lớp vấn đề cho SIMPLEAI
class MazeProblem(SearchProblem):
    def __init__(self, initial, goal, board):
        super().__init__(initial)
        self.goal = goal
        self.board = board

    def actions(self, state):
        x, y = state
        possible_actions = []
        if y > 0 and self.board[y - 1][x] != "#":  # Lên
            possible_actions.append((x, y - 1))
        if y < len(self.board) - 1 and self.board[y + 1][x] != "#":  # Xuống
            possible_actions.append((x, y + 1))
        if x > 0 and self.board[y][x - 1] != "#":  # Trái
            possible_actions.append((x - 1, y))
        if x < len(self.board[0]) - 1 and self.board[y][x + 1] != "#":  # Phải
            possible_actions.append((x + 1, y))
        return possible_actions

    def result(self, state, action):
        return action

    def goal_test(self, state):
        return state == self.goal

    def heuristic(self, state):
        x1, y1 = state
        x2, y2 = self.goal
        return abs(x1 - x2) + abs(y1 - y2)

# Ứng dụng Streamlit
st.title('Tìm đường trong mê cung')

if "dem" not in st.session_state:
    st.session_state["dem"] = 0

if "points" not in st.session_state:
    st.session_state["points"] = []

if "bg_image" not in st.session_state:
    st.session_state["bg_image"] = bg_image

canvas_result = st_canvas(
    stroke_width=1,
    stroke_color='',
    background_image=st.session_state["bg_image"],
    height=IMAGE_HEIGHT,
    width=IMAGE_WIDTH,
    drawing_mode="point",
    point_display_radius=0,
    display_toolbar=False,
)

if st.session_state["dem"] == 2:
    if st.button('Direction'):
        if "directed" not in st.session_state:
            st.session_state["directed"] = True
            x1, y1 = st.session_state["points"][0]
            x2, y2 = st.session_state["points"][1]

            problem = MazeProblem((x1, y1), (x2, y2), MAP)
            result = astar(problem)

            # Lấy đường đi từ kết quả
            path = result.path()
            if path:
                frames = []
                frame = st.session_state["bg_image"].copy()
                for state in path:
                    if isinstance(state, tuple) and len(state) == 2:
                        px, py = state
                        if CELL_WIDTH is not None and CELL_HEIGHT is not None:
                            draw_x = px * CELL_WIDTH + 2
                            draw_y = py * CELL_HEIGHT + 2
                            draw_frame = ImageDraw.Draw(frame)
                            draw_frame.ellipse(
                                [draw_x, draw_y, draw_x + CELL_WIDTH - 4, draw_y + CELL_HEIGHT - 4],
                                fill="#FF00FF", outline="#FF00FF",
                            )
                            frames.append(frame)
                            frame = frame.copy()
                st.session_state["bg_image"] = frame
                frames[0].save("maze_solution.gif", format="GIF", append_images=frames,
                               save_all=True, duration=300)

                st.image("maze_solution.gif")
                st.text('Nhấn Ctrl-R để chạy lại')

# Xử lý canvas
if canvas_result.json_data is not None:
    lst_points = canvas_result.json_data["objects"]
    if len(lst_points) > 0:
        px, py = lst_points[-1]['left'], lst_points[-1]['top']
        if CELL_WIDTH and CELL_HEIGHT:  # Kiểm tra lại trước khi thực hiện phép toán
            x = int(px) // CELL_WIDTH
            y = int(py) // CELL_HEIGHT

            if MAP[y][x] != '#':
                if st.session_state["dem"] < 2:
                    st.session_state["dem"] += 1
                    if st.session_state["dem"] == 1:
                        draw_x, draw_y = x * CELL_WIDTH + 2, y * CELL_HEIGHT + 2
                        frame = st.session_state["bg_image"].copy()
                        draw_frame = ImageDraw.Draw(frame)
                        draw_frame.ellipse(
                            [draw_x, draw_y, draw_x + CELL_WIDTH - 4, draw_y + CELL_HEIGHT - 4],
                            fill="#FF00FF", outline="#FF00FF",
                        )
                        st.session_state["bg_image"] = frame
                        st.session_state["points"].append((x, y))
                        st.rerun()
                    elif st.session_state["dem"] == 2:
                        draw_x, draw_y = x * CELL_WIDTH + 2, y * CELL_HEIGHT + 2
                        frame = st.session_state["bg_image"].copy()
                        draw_frame = ImageDraw.Draw(frame)
                        draw_frame.ellipse(
                            [draw_x, draw_y, draw_x + CELL_WIDTH - 4, draw_y + CELL_HEIGHT - 4],
                            fill="#FF0000", outline="#FF0000",
                        )
                        st.session_state["bg_image"] = frame
                        st.session_state["points"].append((x, y))
                        st.rerun()