import dash
from dash import dcc, html, Input, Output, State, ctx, ALL
import dash_bootstrap_components as dbc
import feffery_antd_components as fac
from datetime import datetime
import uuid
import base64
import os
import json
import atexit
from functions import prompt_based, query_ollama

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
data_folder_path = './data'
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "AI Academic Assistant"
store_prompt = ''
default_convo = [{
    "id": str(uuid.uuid4()),
    "title": "Initial Conversation",
    "messages": [{"role": "assistant", "content": "Start asking your questions!"}],
    "s_id": 0
}]
initial_session_id = str(uuid.uuid4())

# 初始数据文件路径
CONVO_FILE = "data_history/saved_conversations.json"


# 加载历史记录（若存在）
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Loading {path} fail：{e}")
    return default


def get_dropdown_options_from_folder(folder_path):
    options = [
        {'label': folder_name, 'value': folder_name}
        for folder_name in os.listdir(folder_path)
        if os.path.isdir(os.path.join(folder_path, folder_name))
    ]
    return options


def save_file(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(decoded)
    return path

# 保存函数
def save_to_file():
    os.makedirs("data", exist_ok=True)
    with open(CONVO_FILE, "w", encoding="utf-8") as f:
        json.dump(saved_conversations, f, ensure_ascii=False, indent=2)
    print("✅ Using history is downloaded")

initial_convo = load_json(CONVO_FILE, default_convo)
saved_conversations = initial_convo
subject_options = get_dropdown_options_from_folder(data_folder_path)

app.layout = html.Div([
    dcc.Interval(id="interval-update-subjects", interval=5000, n_intervals=0),  # 每5秒检查一次
    dcc.Store(id='theme-store', data='light'),
    dcc.Store(id='chat-history', data=[]),
    dcc.Store(id='saved-conversations', data=initial_convo),
    dcc.Store(id='current-session-id', data=initial_session_id),

    html.Div(id='sync-dummy', style={"display": "none"}),

    # Sidebar
    html.Div([
        dbc.ButtonGroup([
            dbc.Button("☰", id="sidebar-toggle", color="secondary"),
            dbc.Button("💾", id="save-convo", color="success")
        ], vertical=True,
            style={"position": "absolute", "right": "-47px", "top": "50%", "transform": "translateY(-50%)"}),

        html.H4("Chat History", className="p-3 border-bottom"),
        dbc.Button("🧹 Clear All", id="clear-convos", color="danger", style={"width": "100%", "marginBottom": "10px"}),
        html.Div(id="sidebar-history", className="overflow-auto", style={"height": "85vh"})
    ], id="sidebar", style={
        "position": "fixed", "left": "-13vw", "width": "13vw", "height": "100%",
        "transition": "all 0.3s", "backgroundColor": "#f8f9fa", "zIndex": 1000,
        "boxShadow": "2px 0 5px rgba(0,0,0,0.1)"
    }),

    dcc.Loading(
        id="loading-indicator",
        type="circle",  # 或 "dot", "default"
        color="gray",
        children=html.Div(
            id="loading-message",
            children="LOADING...",
            style={
                "display": "none",
                "position": "fixed",
                "bottom": "1.25vh",
                "left": "50%",
                "transform": "translateX(-50%)",
                "background-color": "rgba(0, 0, 0, 0.7)",
                "color": "white",
                "padding": "10px 20px",
                "border-radius": "5px",
                "z-index": "1000"
            }
        )
    ),

    # Main Content
    html.Div([
        dbc.Container([
            dbc.Button("🌙/☀️", id="theme-toggle", color="secondary",
                       style={"position": "fixed", "top": "0.62vh", "right": "0.78vw", "zIndex": 1000}),

            html.Div([
                dcc.Upload(
                    id='file-upload',
                    children=dbc.Button("📎 Upload File", color="secondary"),
                    multiple=False,
                    accept=".pdf"
                )
            ], style={"position": "fixed", "top": "5vh", "right": "0.78vw", "zIndex": 1000}),

            # Chat Card

            dbc.Card([
                dbc.CardHeader(
                    dbc.Row([
                        dbc.Col(html.H5("Current Chat", className="mb-0 text-white"), width="auto"),
                        dbc.Col(
                            dcc.Dropdown(
                                id='subject-dropdown',
                                options=[],  # 初始为空，由 interval 回调自动填充
                                value=None,  # 初始为空，由回调设置默认值
                                clearable=False,
                                style={
                                    'width': '120px',
                                    'fontSize': '0.85rem',
                                    'color': '#000',
                                    'backgroundColor': '#fff'
                                }
                            ), width="auto"
                        )
                    ], align="center", justify="between"),
                    className="bg-primary"
                ),
                dbc.CardBody([
                    dcc.Loading(html.Div([
                        html.Div(id="history-list", className="overflow-auto",
                                 style={"height": "400px", "overflowY": "auto"}),
                        html.Div(id="scroll-anchor")  # 锚点元素
                    ])),
                    dcc.Interval(id='scroll-interval', interval=500, n_intervals=0, max_intervals=0)
                ])
            ], className="mb-4"),

            # Input
            dbc.InputGroup([
                dbc.Input(id="user-input", placeholder="Enter your question...", type="text"),
                dbc.Button("Send", id="send-button", color="primary")
            ], className="mb-3",
                style={"border": "2px solid #ccc", "borderRadius": "10px", "padding": "0px"}),

            # Prompt Box
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div([
                            html.Span("Prompt", id='prompt-header', style={"fontWeight": "bold", "fontSize": "16px"}),
                            fac.AntdSwitch(
                                id='prompt-enable-switch',
                                checkedChildren='Enabled',
                                unCheckedChildren='Forbidden',
                                checked=False,
                                style={'transform': 'scale(0.9)'}
                            )
                        ],
                            style={
                                'display': 'flex',
                                'justifyContent': 'space-between',
                                'alignItems': 'center'
                            })
                    ),

                    fac.AntdInput(
                        id='prompt-input',
                        mode='text-area',
                        autoSize=False,
                        allowClear=True,
                        placeholder='请输入提示词模板：',
                        defaultValue=prompt_based,
                        status=None,  # 动态设置状态 success / error
                        style={
                            'fontSize': 16,
                            'height': '180px',
                            'padding': '15px 0'
                        }
                    ),
                    fac.AntdText(id='prompt-feedback', style={'fontSize': 14, 'marginTop': '4px'}),

                    # 保留下方按钮
                    dbc.InputGroup(
                        [
                            dbc.Button("Submit", id="submit-btn", n_clicks=0, color="primary")
                        ],
                        style={"padding": "10px 0"}
                    )
                ],
                className="mb-4",
                style={
                    "position": "fixed",
                    "top": "10vh", "right": "0.78vw", "width": "12vw"
                }
            )
        ])
    ], id="main-content", style={
        "transition": "all 0.3s"
    },)
], id="main-container", className="light-theme", style={"height": "100vh"})

# Clientside scroll callback
app.clientside_callback(
    """
    function(n_intervals) {
        const anchor = document.getElementById("scroll-anchor");
        if (anchor) {
            anchor.scrollIntoView({ behavior: "smooth", block: "end" });
        }
        return "";
    }
    """,
    Output("scroll-anchor", "children"),
    Input("scroll-interval", "n_intervals")
)


# Theme toggle
@app.callback(
    [Output("theme-store", "data"),
     Output("main-container", "className"),
     Output("prompt-header", "style")],
    Input("theme-toggle", "n_clicks"), prevent_initial_call=True
)
def toggle_theme(n):
    theme = "dark-theme" if n % 2 == 1 else "light-theme"
    header_style = {"color": "#fff"} if theme == "dark-theme" else {"color": "#000"}
    return theme, theme, header_style


# Sidebar toggle
@app.callback(
    [Output("sidebar", "style"), Output("main-content", "style")],
    Input("sidebar-toggle", "n_clicks"), State("sidebar", "style")
)
def toggle_sidebar(n, style):
    if n is None:
        return style, dash.no_update
    is_open = style["left"] == "-13vw"
    new_left = "0" if is_open else "-13vw"
    new_margin = "1.95vw" if is_open else "0"
    style["left"] = new_left
    return style, {"marginLeft": new_margin, "transition": "all 0.3s"}


@app.callback(
    Output("loading-message", "style"),
    [Input("send-button", "n_clicks"), Input("user-input", "n_submit")],
    prevent_initial_call=True
)
def show_loading(n_clicks, n_submit):
    return {
        "display": "block",
        "position": "fixed",
        "bottom": "20px",
        "left": "50%",
        "transform": "translateX(-50%)",
        "background-color": "rgba(0, 0, 0, 0.7)",
        "color": "white",
        "padding": "10px 20px",
        "border-radius": "5px",
        "z-index": "1000"
    }


# Sending messages
@app.callback(
    [Output("chat-history", "data"), Output("user-input", "value")],
    [Input("send-button", "n_clicks"), Input("user-input", "n_submit")],
    [State("user-input", "value"), State("chat-history", "data"), State('subject-dropdown', "value"),
     State('prompt-enable-switch', "checked"), State('current-session-id', 'data')],
    prevent_initial_call=True
)
def handle_send(n_clicks, n_submit, user_input, chat_history, subject, prompt_enable, session_id):
    if not user_input:
        return dash.no_update, dash.no_update

    # Add a loading message temporarily
    loading_msg = {"role": "assistant", "content": "Loading..."}
    chat_history.append({"role": "user", "content": user_input})  # Add user input to chat history
    chat_history.append(loading_msg)  # Add the loading message

    # Call the Ollama model and wait for the response
    print(f'the current session id is {session_id}')
    response = query_ollama(q=user_input, key=subject, session_id=session_id, user_id='', prompt_new=prompt_enable,
                            input_prompt=store_prompt)
    bot_msg = {"role": "assistant", "content": f"{response}"}

    # Replace the loading message with the actual response
    chat_history[-1] = bot_msg  # Replace the "Loading..." message with the bot's response

    return chat_history, ""


# Display history and reset interval
@app.callback(
    [Output("history-list", "children"), Output("loading-message", "style", allow_duplicate=True),
     Output("scroll-interval", "n_intervals", allow_duplicate=True)],
    Input("chat-history", "data"),
    prevent_initial_call=True
)
def display_history(history):
    if not history:
        return html.Div("Start asking your questions!", style={"color": "#888", "padding": "10px"}), {
            "display": "none"}, 0

    items = []
    for msg in history:
        if msg["role"] == "user":
            content_element = html.Span(msg["content"])  # 用户消息为纯文本
        else:
            content_element = dcc.Markdown(msg["content"], style={"whiteSpace": "pre-wrap"})

        items.append(
            html.Div([
                html.Strong("You: " if msg["role"] == "user" else "AI: "),
                content_element
            ], style={
                "marginBottom": "10px",
                "backgroundColor": "#f1f1f1" if msg["role"] == "assistant" else "#d1ecf1",
                "padding": "10px",
                "borderRadius": "5px"
            })
        )

    items.append(html.Div(id="scroll-anchor"))
    return items, {"display": "none"}, 0


# Save conversation
@app.callback(
    [Output("saved-conversations", "data", allow_duplicate=True),
     Output("chat-history", "data", allow_duplicate=True), Output("current-session-id", 'data', allow_duplicate=True)],
    Input("save-convo", "n_clicks"),
    State("chat-history", "data"),
    State("saved-conversations", "data"),
    State("current-session-id", 'data'),
    prevent_initial_call=True
)
def save_chat(n_clicks, chat_history, saved_convos, session_id):
    if not chat_history:
        return dash.no_update, dash.no_update, dash.no_update
    print(f'the saved id is {session_id}')
    new_entry = {
        "id": str(uuid.uuid4()),
        "title": f"Conversation {len(saved_convos) + 1} - {datetime.now().strftime('%m/%d %H:%M')}",
        "messages": chat_history,
        "s_id": session_id
    }
    new_session_id = str(uuid.uuid4())
    print(f'the new session id is {new_session_id}')
    global saved_conversations
    saved_conversations = saved_convos + [new_entry]
    save_to_file()
    return saved_convos + [new_entry], [], new_session_id


# Clear saved conversations
@app.callback(
    Output("saved-conversations", "data"),
    Input("clear-convos", "n_clicks"),
    prevent_initial_call=True
)
def clear_conversations(n_clicks):
    if n_clicks:
        return initial_convo
    return dash.no_update


# Render sidebar list
@app.callback(
    Output("sidebar-history", "children"),
    Input("saved-conversations", "data"),
    Input("theme-store", "data")
)
def render_sidebar(convos, theme):
    items = []
    for convo in convos:
        preview = next((m["content"] for m in convo["messages"] if m["role"] == "user"), "Empty")
        items.append(
            dbc.ListGroupItem(
                [html.Small(convo["title"], className="text-muted"),
                 html.P((preview[:30] + "...") if len(preview) > 30 else preview, className="mb-0")],
                id={"type": "convo-item", "index": convo["id"]}, action=True,
                style={
                    "backgroundColor": "#404040" if theme == "dark" else "white",
                    "color": "#dfe6e9" if theme == "dark" else "#2c3e50"
                }
            )
        )
    return items


# Load selected conversation
@app.callback(
    Output("chat-history", "data", allow_duplicate=True), Output("current-session-id", 'data', allow_duplicate=True),
    Input({'type': 'convo-item', 'index': ALL}, 'n_clicks'),
    State("saved-conversations", "data"),
    prevent_initial_call=True
)
def load_conversation(n_clicks_list, saved):
    triggered = ctx.triggered_id
    if not triggered or "index" not in triggered:
        return dash.no_update, dash.no_update
    convo_id = triggered["index"]
    for convo in saved:
        if convo["id"] == convo_id:
            if convo['title'] == 'Initial Conversation':
                return convo["messages"], dash.no_update
            print(f"the selected id is {convo}\n")
            return convo["messages"], convo_id
    return dash.no_update, dash.no_update


# Handle file upload
@app.callback(
    Output("chat-history", "data", allow_duplicate=True),
    Input("file-upload", "contents"),
    State("file-upload", "filename"),
    State("chat-history", "data"),
    prevent_initial_call=True
)
def handle_file_upload(contents, filename, history):
    if contents is None:
        return dash.no_update
    save_file(contents, filename)
    return history + [{"role": "user", "content": f"(Uploaded file: {filename})"}]


# 添加 Dropdown 动态更新的回调
@app.callback(
    [Output("subject-dropdown", "options"),
     Output("subject-dropdown", "value")],
    Input("interval-update-subjects", "n_intervals"),
    prevent_initial_call=False
)
def update_subject_dropdown(n_intervals):
    from functions import get_dropdown_options_from_folder
    folder = './data'
    options = get_dropdown_options_from_folder(folder)
    if not options:
        return [], None
    return options, options[0]['value']


# @app.callback(
#     [Output("prompt-box", "children"),
#      Output("prompt-input", "value")],
#     Input("submit-btn", "n_clicks"),
#     State("user-input", "value"),
#     prevent_initial_call=True
# )
# def update_prompt(n_clicks, prompt_input):
#     try:
#         filled_prompt = prompt_input.format(q=" ", source=' ')
#     except (KeyError, ValueError, AttributeError) as e:
#         return html.P("❌ Prompt 格式错误：请输入包含 {q} 的有效模板字符串。", style={"color": "red"}), ""
#
#     return html.P(f"✅ Updated Prompt：{prompt_input}", style={"color": "#333"}), ""


# 回调
@app.callback(
    Output('prompt-input', 'status'),
    Output('prompt-feedback', 'children'),
    Output('prompt-feedback', 'type'),
    Input('submit-btn', 'n_clicks'),
    State('prompt-input', 'value'),
    State('prompt-enable-switch', 'checked'),
)
def validate_prompt(n_clicks, value, checked):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    if not checked:
        return None, "The prompt template is not enabled", "warning"
    if value and '{q}' in value and 'source' in value:
        store_prompt = value
        print(store_prompt)
        return None, '✅ Prompt changing successfully', 'success'
    else:
        return 'error', '❌ Your prompt must include {q} and {source}', 'danger'





# 定期更新数据（可以绑定前端 Store 的变化）
@app.callback(
    Output('sync-dummy', 'children'),  # hidden div 占位
    Input('saved-conversations', 'data'),
    prevent_initial_call=True
)
def sync_data_to_server(convos):
    global saved_conversations
    saved_conversations = convos
    print(saved_conversations)
    return ""





atexit.register(save_to_file)

if __name__ == "__main__":
    app.run(debug=True)
