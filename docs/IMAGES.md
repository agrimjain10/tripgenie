# Photography

Wandiamo combines real destination photographs with clearly labelled AI travel inspiration. Images are downloaded into `frontend/public/images` so page rendering does not depend on a third-party image server. A photo may represent the named destination or general landscape/travel inspiration; generic images are labeled as inspiration in discovery.

## Sources

| Asset | Source |
| --- | --- |
| Jaipur / Amber Fort | [Unsplash image](https://images.unsplash.com/photo-1599661046827-dacff0c0f09a) |
| Goa | [Unsplash image](https://images.unsplash.com/photo-1512343879784-a960bf40e7f2) |
| Agra / Taj Mahal | [Unsplash image](https://images.unsplash.com/photo-1564507592333-c60657eea523) |
| Kerala backwaters | [Unsplash image](https://images.unsplash.com/photo-1602216056096-3b40cc0c9944) |
| Mumbai / Gateway of India | [Unsplash image](https://images.unsplash.com/photo-1595658658481-d53d3f999875) |
| Amritsar / Golden Temple | [Unsplash image](https://images.unsplash.com/photo-1514222134-b57cbb8ce073) |
| Chandigarh / Sukhna Lake | [Picture & Poet on Unsplash](https://unsplash.com/photos/a-large-body-of-water-with-trees-in-the-background-TF-5cYpNzFo) |
| Dharamshala / Dhauladhar mountains | [Abhinav Goswami on Pexels](https://www.pexels.com/photo/dhauladhar-mountains-at-sunrise-dharamshala-view-36966952/) |
| Travel inspiration | [Unsplash image](https://images.unsplash.com/photo-1488646953014-85cb44e25828) |
| Existing mountains, lake, coast and city assets | Retained Unsplash photography from the original travel workspace; used as landscape inspiration |

See the [Unsplash license](https://unsplash.com/license) and [Pexels license](https://www.pexels.com/license/). Destination copy and inspiration photographs do not guarantee views, weather, property affiliation or access.

## AI artwork and destination covers

`frontend/public/images/wandiamo-ai-summit.webp` was created with the built-in imagegen tool. Prompt: cinematic Himalayan-inspired alpine summit on the right, teal/forest shadows, snowy foreground, soft peach clouds, sage sky, natural photographic texture, no text or people. This is imaginative travel inspiration, not a documentary view of a named destination. Authentication uses the same labelled artwork.

Each owned trip offers **Create AI cover**. The server sends only destination and interests to Gemini, with `GEMINI_IMAGE_MODEL` (default `gemini-3.1-flash-image`) and `GEMINI_IMAGE_API_KEY` or the existing Gemini key. Image model access/quota is separate from text generation and may require a paid Google account. Wandiamo does not enable billing. A quota/access error leaves the original photo and trip intact.

Covers are compressed to JPEG, cached in the private database, never included in trip lists or public shares, and removed with their trip. Requests are authenticated, limited to one attempt per minute per trip and five distinct trip cover requests per account per rolling day. Creation is explicitly requested by the traveler, never silently triggered by a page view. A cached successful cover is reused.
