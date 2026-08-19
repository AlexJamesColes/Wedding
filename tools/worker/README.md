# The drop

Guests' photographs and films, received from coleswedding.com/your-photographs
into a private Cloudflare R2 bucket through the Worker in photographs.js.

## Opening it (once)

1. Sign in at dash.cloudflare.com, open R2 and complete its checkout (free
   tier; it asks for a card but usage at this scale costs pence).
2. From this folder:

       npx wrangler login
       npx wrangler r2 bucket create ca-photographs --jurisdiction eu
       npx wrangler deploy

   The last line prints the Worker's address, https://ca-photographs.<name>.workers.dev.
3. Paste that address into `var ENDPOINT = ''` in /your-photographs.html and
   push; the page opens.

## Afterwards

- Browse or download in the dashboard (R2 > ca-photographs), or pull the lot:

       npx wrangler r2 object get ... (one at a time)
       # or rclone, with an R2 API token: rclone copy r2:ca-photographs ~/Wedding/Photographs

- Each object's metadata carries guest, mark, original filename and date;
  keys never carry names.
- To close: change CLOSES in wrangler.toml and `npx wrangler deploy`, or delete
  the Worker. Emptying the bucket afterwards ends any storage charge.
- After any change to the door list in assets/gate.js, run
  `python3 build_wrangler.py` and redeploy so the Worker admits the same names.
