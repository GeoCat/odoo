/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { loadJS, loadCSS } from "@web/core/assets";

// Makes sure that the Quill assets are loaded only once
let quillLoaded = false;

// TODO: Doing this in an OWL Component would perhaps be more future-proof,
//       but difficult to use if we wish to keep the existing textareas and all their attributes (e.g. id).
//       We need to keep the attributes else the form submission will not work correctly.
publicWidget.registry.richTextForm = publicWidget.Widget.extend({
    // Apply to text areas with classes "o_wysiwyg_loader" AND "rich_text"
    selector: "textarea.o_wysiwyg_loader.rich_text",

    async start() {
        const result = await this._super(...arguments);

        if (!quillLoaded) {
            console.log("Loading Quill for rich text editing...");
            // Load Quill.js and its CSS onto window interface
            await Promise.all([
                loadJS("https://cdn.jsdelivr.net/npm/quill@2.0.3/dist/quill.js"),
                loadCSS("https://cdn.jsdelivr.net/npm/quill@2.0.3/dist/quill.snow.css"),
            ]);

            // noinspection JSUnresolvedReference
            if (typeof window.Quill === 'undefined') {
                // If Quill.js is not available, remove the o_wysiwyg_loader class from the textarea and
                // if there is an o_wysiwyg_textarea_wrapper, move the textarea out of it and remove the wrapper.
                // Otherwise, users will keep seeing the loading spinner indefinitely and cannot edit the textarea.
                this.$target.removeClass("o_wysiwyg_loader");
                const $wrapper = this.$target.closest(".o_wysiwyg_textarea_wrapper");
                if ($wrapper.length) {
                    this.$target.insertBefore($wrapper);
                    $wrapper.remove();
                }

                // Log to console (but do not notify user)
                console.error("Quill library failed to load. Rich text editing will not be available.");
                return result;
            }

            console.log("Quill loaded successfully.");
            quillLoaded = true;
        }

        // For each textarea, we will create a Quill editor instance
        this.$target.each((_, textarea) => {
            const $textarea = $(textarea);
            const $wrapper = $textarea.closest(".o_wysiwyg_textarea_wrapper");
            // Return if the textarea (or its wrapper) is hidden:
            // this could mean that we already have a rich text editor initialized
            if ($textarea.is(":hidden")) {
                return;
            }

            // Quill needs a container to render the editor in.
            // That will also add a div *before* that for the toolbar module.
            // We want them both to be wrapped inside a richTextArea container so they stay together.
            const richTextArea = document.createElement("div");
            richTextArea.className = "rich-text-area";
            richTextArea.hidden = true;

            // Create the quillContainer and add it to the richTextArea
            const quillContainer = document.createElement("div");
            richTextArea.appendChild(quillContainer);

            // Hack to add a proper "code-block" button to the Quill toolbar that differs from the "code" button
            // See https://github.com/slab/quill/pull/3917 and https://github.com/slab/quill/issues/3165
            // noinspection JSUnresolvedReference
            const icons = window.Quill.import('ui/icons');
            icons['code-block'] = '<svg viewbox="0 -2 15 18">\n' + '\t<polyline class="ql-even ql-stroke" points="2.48 2.48 1 3.96 2.48 5.45"/>\n' + '\t<polyline class="ql-even ql-stroke" points="8.41 2.48 9.9 3.96 8.41 5.45"/>\n' + '\t<line class="ql-stroke" x1="6.19" y1="1" x2="4.71" y2="6.93"/>\n' + '\t<polyline class="ql-stroke" points="12.84 3 14 3 14 13 2 13 2 8.43"/>\n' + '</svg>';

            // Set up the Quill editor in the quillContainer
            // noinspection JSUnresolvedReference
            const quillEditor = new window.Quill(quillContainer, {
                modules: {
                    toolbar: [
                        ['bold', 'italic', 'underline', 'strike'],
                        ['link', 'blockquote', 'code', 'code-block'],
                        [{list: 'ordered'}, {list: 'bullet'}],
                    ],
                },
                theme: 'snow',
            });

            // Insert and unhide the richTextArea, hide the original textarea
            if ($wrapper.length > 0) {
                $wrapper.before(richTextArea);
                $wrapper.hide();
            } else {
                // If there is no wrapper, we will just hide the textarea
                $textarea.before(richTextArea);
                $textarea.hide();
            }
            richTextArea.hidden = false;

            // Update textarea value on blur (because form submit event is triggered *after* odoo checks the form!)
            quillContainer.addEventListener('blur', () => {
                const quillContent = quillEditor.root.innerHTML;
                $textarea.val(quillContent);
            }, true);
        });

        return result;
    }
});

export default publicWidget.registry.richTextForm;
