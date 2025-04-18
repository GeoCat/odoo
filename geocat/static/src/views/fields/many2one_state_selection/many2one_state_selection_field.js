import {Component} from "@odoo/owl";
import {Dropdown} from "@web/core/dropdown/dropdown";
import {DropdownItem} from "@web/core/dropdown/dropdown_item";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {formatText} from "@web/views/fields/formatters";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

export class Many2oneStateSelectionField extends Component {
    static template = "geocat.Many2oneStateSelectionField";
    static components = {
        Dropdown,
        DropdownItem,
    };
    static props = {
        ...standardFieldProps,
        showLabel: {type: Boolean, optional: true},
        autosave: {type: Boolean, optional: true},
        statesField: {type: String, optional: false},
        defaultLabel: {type: String, optional: true},
        defaultColor: {type: String, optional: true},
    };
    static defaultProps = {
        showLabel: true,
        defaultLabel: _t("Normal"),
        defaultColor: "#ccc",
    };

    get defaultState() {
        return {
            id: null,
            name: this.props.defaultLabel,
            color: this.props.defaultColor
        }
    }

    get availableStates() {
        return this.props.record.data[this.props.statesField] || [];
    }

    get options() {
        let result = [this.defaultState];
        return result.concat(this.availableStates);
    }

    get currentState() {
        const stateId = this.props.record.data[this.props.name][0];
        if (!stateId || this.availableStates.length === 0) {
            return this.defaultState;
        }
        return this.options.find((state) => state.id === stateId) || this.defaultState;
    }

    get label() {
        return formatText(this.currentState.name);
    }

    async updateRecord(stateId) {
        await this.props.record.update(
            {[this.props.name]: stateId === null ? false : [stateId,]},
            {save: this.props.autosave}
        );
    }
}

export const many2OneStateSelectionField = {
    component: Many2oneStateSelectionField,
    displayName: _t("Many2one State Selection"),
    supportedOptions: [
        {
            label: _t("Autosave"),
            name: "autosave",
            type: "boolean",
            default: true,
            help: _t(
                "If checked, the record will be saved immediately when the field is modified."
            ),
        },
        {
            label: _t("Hide label"),
            name: "hide_label",
            type: "boolean",
        },
        {
            label: _t("Filtered States Field"),
            name: "states_field",
            type: "array",
            help: _t(
                "JSON field that contains all (filtered) states to be displayed in the dropdown."
            ),
        },
        {
            label: _t("Default State Label"),
            name: "default_label",
            type: "string",
            default: _t("Normal"),
            help: _t(
                "Label to show when no state has been selected."
            ),
        },
        {
            label: _t("Default State Color"),
            name: "default_color",
            type: "string",
            default: "#ccc",
            help: _t(
                "Color to use when no state has been selected."
            ),
        }
    ],
    supportedTypes: ["many2one"],
    extractProps({options, viewType}, dynamicInfo) {
        return {
            showLabel: 'hide_label' in options ? !options.hide_label : false,
            readonly: dynamicInfo.readonly,
            autosave: "autosave" in options ? !!options.autosave : true,
            statesField: "states_field" in options ? options.states_field : [],
            defaultLabel: "default_label" in options ? options.default_label : _t("Normal"),
            defaultColor: "default_color" in options ? options.default_color : "#ccc",
        };
    },
};

registry.category("fields").add("many2one_state_selection", many2OneStateSelectionField);