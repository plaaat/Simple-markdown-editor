import flet as ft
import requests
import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError

def main(page: ft.Page):
    page.title = "Markdown Editor"  # title of the AppBar with a white color
    page.theme_mode = "dark"    # dark mode

    s3_client = None  # Will be initialized later

    def initialize_s3_client():
        nonlocal s3_client
        try:
            s3_client = boto3.client(
                "s3",
                endpoint_url=r2_endpoint_field.value,
                aws_access_key_id=r2_access_key_field.value,
                aws_secret_access_key=r2_secret_key_field.value
            )
            ft.dialog_alert(page, "S3 Client initialized successfully.")
        except Exception as e:
            ft.dialog_alert(page, f"Failed to initialize S3 client: {e}")

    def fetch_posts(e):
        """Fetch posts from the API and populate JSON editor."""
        try:
            response = requests.get(api_url_field.value)
            response.raise_for_status()
            posts = response.json()
            json_editor.value = json.dumps(posts, indent=4, ensure_ascii=False)
            ft.dialog_alert(page, "Posts fetched successfully!")
            page.update()
        except requests.RequestException as e:
            ft.dialog_alert(page, f"Failed to fetch posts: {e}")

    def post_json(updated_posts):
        """Send updated JSON data back to the API."""
        try:
            response = requests.post(api_url_field.value, json=updated_posts)
            response.raise_for_status()
            ft.dialog_alert(page, "Posts updated successfully!")
        except requests.RequestException as e:
            ft.dialog_alert(page, f"Failed to update posts: {e}")

    def post_markdown_to_r2(contentnum, markdown_content):
        """Upload a markdown file to R2 bucket."""
        file_name = f"{contentnum}.md"
        try:
            # Check if the file already exists
            response = s3_client.list_objects_v2(Bucket=r2_bucket_name_field.value, Prefix=file_name)
            if 'Contents' in response:
                # Delete the existing file
                s3_client.delete_object(Bucket=r2_bucket_name_field.value, Key=file_name)
                ft.dialog_alert(page, f"Existing file {file_name} deleted.")

            # Upload the new file
            s3_client.put_object(Bucket=r2_bucket_name_field.value, Key=file_name, Body=markdown_content)
            ft.dialog_alert(page, f"Markdown uploaded successfully as {file_name}.")

        except (BotoCoreError, ClientError) as e:
            ft.dialog_alert(page, f"Failed to upload markdown to R2: {e}")

    def update_preview(e):
        """Updates the preview when the text field content changes."""
        md.value = text_field.value
        page.update()

    def save_changes(e):
        """Save updated JSON data."""
        try:
            updated_data = json.loads(json_editor.value)
            post_json(updated_data)
        except json.JSONDecodeError:
            ft.dialog_alert(page, "Invalid JSON format")

    def upload_markdown(e):
        """Upload the markdown content to R2."""
        try:
            contentnum = int(contentnum_field.value)
            post_markdown_to_r2(contentnum, text_field.value)
        except ValueError:
            ft.dialog_alert(page, "Invalid content number")

    # API and R2 Configuration Fields
    api_url_field = ft.TextField(label="API URL", value="https://<your-json-url>", width=400)
    r2_endpoint_field = ft.TextField(label="R2 Endpoint", value="https://<your-r2-endpoint>", width=400)
    r2_bucket_name_field = ft.TextField(label="Bucket Name", value="<your-bucket-name>", width=400)
    r2_access_key_field = ft.TextField(label="Access Key", value="<your-access-key>", width=400)
    r2_secret_key_field = ft.TextField(label="Secret Key", value="<your-secret-key>", password=True, width=400)

    # UI Components
    text_field = ft.TextField(
        value="## Hello from Markdown",
        multiline=True,
        on_change=update_preview,
        expand=True,
        border_color=ft.colors.with_opacity(0.0,'#ffffff'),
    )
    md = ft.Markdown(
        value=text_field.value,
        selectable=True,
        extension_set="gitHubWeb",
        on_tap_link=lambda e: page.launch_url(e.data),
    )

    json_editor = ft.TextField(
        value="",
        multiline=True,
        expand=True,
        border_color=ft.colors.with_opacity(0.0,'#ffffff'),
        label="Edit Posts JSON",
    )

    contentnum_field = ft.TextField(
        value="",
        label="Content Number",
        width=200
    )

    # Layout

    page.add(
        ft.Row(
            controls=[
                text_field,
                ft.VerticalDivider(color='#567c9c'),
                ft.Container(
                    ft.Column(
                        [md],
                        scroll="hidden",
                    ),
                    expand=True,
                    alignment=ft.alignment.top_left,
                )
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        )
    )

    page.add(
        ft.Row(
            controls=[
                api_url_field,
                r2_endpoint_field,
                r2_bucket_name_field,
            ],
            spacing=10
        )
    )

    page.add(
        ft.Row(
            controls=[
                r2_access_key_field,
                r2_secret_key_field,
                ft.ElevatedButton("Fetch JSON", on_click=fetch_posts),
                ft.ElevatedButton("Initialize", on_click=initialize_s3_client)
            ],
            spacing=10
        )
    )

    page.add(
        ft.Row(
            controls=[
                json_editor,
                ft.Column(
                    controls=[
                        ft.ElevatedButton("Save JSON", on_click=save_changes),
                        ft.ElevatedButton("Upload Markdown", on_click=upload_markdown),
                        contentnum_field
                    ],
                    spacing=10
                )
            ],
            expand=True
        )
    )

ft.app(target=main)
