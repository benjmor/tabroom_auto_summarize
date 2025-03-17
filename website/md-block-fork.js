/**
 * <md-block> custom element
 * @author Lea Verou and Multivalence
 */

import { marked } from 'https://cdn.jsdelivr.net/npm/marked@15.0.7/lib/marked.esm.js';

let DOMPurify = window.DOMPurify;
let Prism = window.Prism;


class SimpleSlugger {
	constructor() {
		this.seen = {};
	}
	slug(text) {
		let slug = text.toString().toLowerCase().trim().replace(/[^\w]+/g, '-');
		if (this.seen[slug]) {
			slug += '-' + this.seen[slug]++;
		} else {
			this.seen[slug] = 1;
		}
		return slug;
	}
}

export const URLs = {
	DOMPurify: "https://cdn.jsdelivr.net/npm/dompurify@2.3.4/dist/purify.es.min.js"
};

// Fix indentation
function deIndent(text) {
	let indent = text.match(/^[\r\n]*([\t ]+)/);

	if (indent) {
		indent = indent[1];

		text = text.replace(RegExp("^" + indent, "gm"), "");
	}

	return text;
}

export class MarkdownElement extends HTMLElement {
	constructor() {
		super();

		// Create a shallow copy of the static renderer and bind its methods.
		this.renderer = Object.assign({}, this.constructor.renderer);
		for (let property in this.renderer) {
			this.renderer[property] = this.renderer[property].bind(this);
		}
	}

	get rendered() {
		return this.getAttribute("rendered");
	}

	get mdContent() {
		return this._mdContent;
	}

	set mdContent(html) {
		this._mdContent = html;
		this._contentFromHTML = false;
		this.render();
	}

	connectedCallback() {
		Object.defineProperty(this, "untrusted", {
			value: this.hasAttribute("untrusted"),
			enumerable: true,
			configurable: false,
			writable: false
		});

		if (this._mdContent === undefined) {
			this._contentFromHTML = true;
			this._mdContent = deIndent(this.innerHTML);
			// marked expects markdown quotes (>) to be un-escaped, otherwise they won't render correctly
			this._mdContent = this._mdContent.replace(/&gt;/g, '>');
		}

		this.render();
	}

	async render() {
		if (!this.isConnected || this._mdContent === undefined) {
			return;
		}

		// Use the element's custom renderer
		marked.use({
			langPrefix: "language-",
			renderer: this.renderer
		});

		let html = this._parse();

		if (this.untrusted) {
			let mdContent = this._mdContent;
			html = await MarkdownElement.sanitize(html);
			if (this._mdContent !== mdContent) {
				// While we were running this async call, the content changed. Abort mission!
				return;
			}
		}

		this.innerHTML = html;

		if (!Prism && URLs.Prism && this.querySelector("code")) {
			Prism = import(URLs.Prism);
			if (URLs.PrismCSS) {
				let link = document.createElement("link");
				link.rel = "stylesheet";
				link.href = URLs.PrismCSS;
				document.head.appendChild(link);
			}
		}

		if (Prism) {
			await Prism; // in case it's still loading
			Prism.highlightAllUnder(this);
		}

		if (this.src) {
			this.setAttribute("rendered", this._contentFromHTML ? "fallback" : "remote");
		} else {
			this.setAttribute("rendered", this._contentFromHTML ? "content" : "property");
		}

		// Fire event
		let event = new CustomEvent("md-render", { bubbles: true, composed: true });
		this.dispatchEvent(event);
	}

	static async sanitize(html) {
		if (!DOMPurify) {
			DOMPurify = import(URLs.DOMPurify).then(m => m.default);
		}
		DOMPurify = await DOMPurify; // in case it's still loading
		return DOMPurify.sanitize(html);
	}
}

export class MarkdownSpan extends MarkdownElement {
	constructor() {
		super();
	}

	_parse() {
		return marked.parseInline(this._mdContent);
	}

	static renderer = {
		codespan(code) {
			if (code.text !== undefined) {
				code = code.text
			} else {
				return `<code>""</code>`;
			}
			if (this._contentFromHTML) {
				// Inline HTML code needs to be escaped to not be parsed as HTML by the browser.
				// Marked double-escapes it, so we need to unescape it.
				code = code.toString().replace(/&amp;(?=[lg]t;)/g, "&");
			} else {
				// Remote code may include characters that need to be escaped to be visible in HTML.
				code = code.toString().replace(/</g, "&lt;");
			}
			return `<code>${code}</code>`;
		}
	}
}

export class MarkdownBlock extends MarkdownElement {
	constructor() {
		super();
	}

	get src() {
		return this._src;
	}

	set src(value) {
		this.setAttribute("src", value);
	}

	get hmin() {
		return this._hmin || 1;
	}

	set hmin(value) {
		this.setAttribute("hmin", value);
	}

	get hlinks() {
		return this._hlinks ?? null;
	}

	set hlinks(value) {
		this.setAttribute("hlinks", value);
	}

	_parse() {
		return marked.parse(this._mdContent);
	}

	static renderer = Object.assign({
		heading(obj) {
			let { depth, text } = obj;
			const headingText = String(text);

			depth = Math.min(6, depth + (this.hmin - 1));

			// Create a slugger instance (a shared instance would be better if you have multiple headings)
			const slugger = new SimpleSlugger();
			const id = slugger.slug(headingText);

			let hlinks = this.hlinks;
			let content;

			if (hlinks === null) {
				content = headingText;
			} else {
				content = `<a href="#${id}" class="anchor">`;
				if (hlinks === "") {
					content += headingText + "</a>";
				} else {
					content += hlinks + "</a>" + headingText;
				}
			}
			return `<h${depth} id="${id}">${content}</h${depth}>`;
		},

		code(code) {
			
			if (code.text !== undefined) {
				code = code.text;
			} else {
				return `<pre><code></code></pre>`;
			}

			if (this._contentFromHTML) {
				// Inline HTML code needs to be escaped to not be parsed as HTML by the browser.
				// Marked double-escapes it, so we need to unescape it.
				code = code.replace(/&amp;(?=[lg]t;)/g, "&");
			} else {
				// Remote code may include characters that need to be escaped to be visible in HTML.
				code = code.replace(/</g, "&lt;");
			}
			return `<pre><code>${code}</code></pre>`;
		}
	}, MarkdownSpan.renderer);

	static get observedAttributes() {
		return ["src", "hmin", "hlinks"];
	}

	attributeChangedCallback(name, oldValue, newValue) {
		if (oldValue === newValue) {
			return;
		}

		switch (name) {
			case "src":
				let url;
				try {
					url = new URL(newValue, location);
				} catch (e) {
					return;
				}

				let prevSrc = this.src;
				this._src = url;

				if (this.src !== prevSrc) {
					fetch(this.src)
						.then(response => {
							if (!response.ok) {
								throw new Error(`Failed to fetch ${this.src}: ${response.status} ${response.statusText}`);
							}
							return response.text();
						})
						.then(text => {
							this.mdContent = text;
						})
						.catch(e => { });
				}
				break;
			case "hmin":
				if (newValue > 0) {
					this._hmin = +newValue;
					this.render();
				}
				break;
			case "hlinks":
				this._hlinks = newValue;
				this.render();
		}
	}
}

customElements.define("md-block", MarkdownBlock);
customElements.define("md-span", MarkdownSpan);