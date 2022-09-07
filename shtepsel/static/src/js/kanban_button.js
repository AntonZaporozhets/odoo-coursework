odoo.define('button_near_create.kanban_button', function(require) {
   "use strict";
   var KanbanController = require('web.KanbanController');
   var KanbanView = require('web.KanbanView');
   var viewRegistry = require('web.view_registry');
   var ConfirmButton = KanbanController.include({
       buttons_template: 'button_near_create.button',
       events: _.extend({}, KanbanController.prototype.events, {
           'click .confirm_action_kanban': '_ConfirmKanban',
       }),
       _ConfirmKanban: function () {
       var self = this;
        this.do_action('shtepsel.shtepsel_route_create_wizard_server_action');
   }
   });
   var RefreshButton = KanbanController.include({
       buttons_template: 'button_near_create.button',
       events: _.extend({}, KanbanController.prototype.events, {
           'click .refresh_action_kanban': '_RefreshKanban',
       }),
       _RefreshKanban: function () {
       var self = this;
        this.do_action('shtepsel.shtepsel_refresh_constructor_wizard_server_action');
   }
   });
   var WizardKanbanView = KanbanView.extend({
       config: _.extend({}, KanbanView.prototype.config, {
           Controller: ConfirmButton, RefreshButton
       }),
   });
   viewRegistry.add('button_in_kanban', WizardKanbanView);
});
