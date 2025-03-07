import { DiscussCoreWeb } from "@mail/discuss/core/web/discuss_core_web_service";
import { patch } from "@web/core/utils/patch";

// noinspection JSValidateTypes
/** @type {import("models").DiscussCoreWeb} **/
const discussCoreWebPatch = {
    setup() {
        // NOTE: This overrides Odoo's DiscussCoreWeb.setup method
        // so that it does not subscribe to the "res.users/connection" event,
        // which causes the chat window to pop up when a new user connects.
        // The code below is a 1:1 copy of the original method, minus that subscribe call.

        // noinspection DuplicatedCode
        this.busService.subscribe("discuss.Thread/fold_state", async (data) => {
            const thread = await this.store.Thread.getOrFetch(data);
            if (data.fold_state && thread && data.foldStateCount > thread.foldStateCount) {
                thread.foldStateCount = data.foldStateCount;
                thread.state = data.fold_state;
                if (thread.state === "closed") {
                    const chatWindow = this.store.ChatWindow.get({ thread });
                    chatWindow?.close({ notifyState: false });
                }
            }
        });
        this.env.bus.addEventListener("mail.message/delete", ({ detail: { message } }) => {
            if (message.thread?.model === "discuss.channel") {
                // initChannelsUnreadCounter becomes unreliable
                this.store.channels.fetch();
            }
        });
        this.busService.start();
    }
};

patch(DiscussCoreWeb.prototype, discussCoreWebPatch);