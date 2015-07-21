Pcs = Ember.Application.createWithMixins({
  LOG_TRANSITIONS: true,
  cluster_name: get_cluster_name(),
  cluster_settings: null,
  cur_page: "",
  opening_resource: "",
  opening_node: "",
  opening_aclrole: "",
  resource_page: function() {
    if (this.cur_page == "resources") return "display: table-row;";
    else return "display: none;";
  }.property("cur_page"),
  node_page: function() {
    if (this.cur_page == "nodes") return "display: table-row;";
    else return "display: none;";
  }.property("cur_page"),
  stonith_page: function() {
    if (this.cur_page == "stonith") return "display: table-row;";
    else return "display: none;";
  }.property("cur_page"),
  configure_page: function() {
    if (this.cur_page == "configure") return "display: table-row;";
    else return "display: none;";
  }.property("cur_page"),
  acls_page: function() {
    if (this.cur_page == "acls") return "display: table-row;";
    else return "display: none;";
  }.property("cur_page"),
  manage_page: function() {
    if (this.cur_page == "manage") return "display: table-row;";
    else return "display: none;";
  }.property("cur_page"),
  wizards_page: function() {
    if (this.cur_page == "wizards") return "display: table-row;";
    else return "display: none;";
  }.property("cur_page"),

  getResourcesFromID: function(resources) {
    var retArray = [];
    var resource_map = Pcs.resourcesContainer.get('resource_map');
    $.each(resources, function(_, resource_id) {
      if (resource_id in resource_map && !resource_map[resource_id].get('stonith')) {
        retArray.pushObject(resource_map[resource_id]);
      }
    });
    return retArray;
  },
  update_timeout: null,
  update: function(first_run) {
    if (window.location.pathname.lastIndexOf('/manage', 0) !== 0) {
      return;
    }
    clearTimeout(Pcs.update_timeout);
    var self = Pcs;
    if (first_run)
      show_loading_screen();
    var cluster_name = self.cluster_name;
    if (cluster_name == null) {
      Ember.debug("Empty Cluster Name");
      $.ajax({
        url: "/clusters_overview",
        dataType: "json",
        timeout: 20000,
        success: function(data) {
          Pcs.clusterController.update(data);
          Ember.run.next(function(){correct_visibility_dashboard(Pcs.clusterController.cur_cluster);});
          if (data["not_current_data"]) {
            self.update();
          } else {
            Pcs.update_timeout = window.setTimeout(self.update, 20000);
          }
          hide_loading_screen();
        },
        error: function(jqhxr,b,c) {
          if (jqhxr.responseText) {
            try {
              var obj = $.parseJSON(jqhxr.responseText);
              if (obj.notauthorized == "true") {
                location.reload();
              }
            } catch(e) {
              console.log("Error: Unable to parse json for clusters_overview");
            }
          }
          Pcs.update_timeout = window.setTimeout(self.update,20000);
          hide_loading_screen();
        }
      });
      return;
    }
    $.ajax({
      url: "cluster_status",
      dataType: "json",
      success: function(data) {
        Pcs.resourcesContainer.update(data);
        Pcs.nodesController.update(data);
        Pcs.settingsController.update(data);
        Pcs.aclsController.update(data);
        Pcs.set("cluster_settings",data.cluster_settings);
        Pcs.set('need_ring1_address', false);
        Pcs.set('is_cman_with_udpu_transport', false);
        if (data['need_ring1_address']) {
          Pcs.set('need_ring1_address', true);
        }
        if (data['is_cman_with_udpu_transport']) {
          Pcs.set('is_cman_with_udpu_transport', true);
        }
        var fence_change = false;
        var resource_change = false;
        Ember.run.next(function () {
          var self = Pcs.resourcesContainer;
          var cur_fence = self.get('cur_fence');
          var cur_resource = self.get('cur_resource');
          var resource_map = self.get('resource_map');
          if (first_run) {
            Pcs.nodesController.load_node($('#node_list_row').find('.node_selected').first(),true);
            Pcs.aclsController.load_role($('#acls_list_row').find('.node_selected').first(), true);
            if (self.get("fence_id_to_load")) {
              cur_fence = self.get_resource_by_id(self.get("fence_id_to_load"));
              fence_change = true;
            }
            if (self.get("resource_id_to_load")) {
              cur_resource = self.get_resource_by_id(self.get("resource_id_to_load"));
              resource_change = true;
            }
          }

          if (cur_fence && cur_fence.get('id') in resource_map) {
            if (resource_map[cur_fence.get('id')] !== cur_fence) {
              cur_fence = resource_map[cur_fence.get('id')];
            }
          } else {
            if (self.get('fence_list').length > 0) {
              cur_fence = self.get('fence_list')[0];
              fence_change = true;
            }
          }

          if (cur_resource && cur_resource.get('id') in resource_map) {
            if (resource_map[cur_resource.get('id')] !== cur_resource) {
              cur_resource = resource_map[cur_resource.get('id')];
            }
          } else {
            if (self.get('resource_list').length > 0) {
              cur_resource = self.get('resource_list')[0];
              resource_change = true;
            }
          }

          self.set('cur_fence', cur_fence);
          self.set('cur_resource', cur_resource);

          Ember.run.scheduleOnce('afterRender', Pcs, function () {
            if (fence_change)
              tree_view_onclick(self.get('cur_fence').get('id'), true);
            if (resource_change)
              tree_view_onclick(self.get('cur_resource').get('id'), true);
            if (!fence_change && self.get('cur_fence'))
              tree_view_select(self.get('cur_fence').get('id'));
            if (!resource_change && self.get('cur_fence'))
              tree_view_select(self.get('cur_resource').get('id'));
            Pcs.selectedNodeController.reset();
            setup_node_links();
            disable_checkbox_clicks();
          });
        });
      },
      error: function(jqhxr,b,c) {
        try {
          var obj = $.parseJSON(jqhxr.responseText);
          if (obj.notauthorized == "true") {
            location.reload();
          }
        } catch(e) {
          console.log("Error: Unable to parse json for cluster_status")
        }
      },
      complete: function() {
        hide_loading_screen();
        Pcs.update_timeout = window.setTimeout(Pcs.update,20000);
      }
    });
  }
});

Pcs.resourcesContainer = Ember.Object.create({
  resource_map: {},
  top_level_resource_map: {},
  fence_list: [],
  resource_list: [],
  resource_id_to_load: null,
  fence_id_to_load: null,
  cur_resource: null,
  cur_fence: null,
  constraints: {},
  group_list: [],

  get_resource_by_id: function(resource_id) {
    var resource_map = this.get('resource_map');
    if (resource_id in resource_map)
      return resource_map[resource_id];
    return null;
  },

  get_family_list: function(parent) {
    var family = [];
    family.push(parent);
    switch (parent["class_type"]) {
      case "group":
        $.each(parent.get('members'), function(index, member) {
          family = family.concat(Pcs.resourcesContainer.get_family_list(member));
        });
        break;
      case "clone":
      case "master":
        family = family.concat(Pcs.resourcesContainer.get_family_list(parent.get('member')));
        break;
    }
    return family;
  },

  get_constraints: function(cons) {
    var ord_con = {};
    var loc_con = {};
    var col_con = {};
    var ord_set_con = {};
    var res_loc_constraints = {};
    var res_ord_constraints = {};
    var res_ord_set_constraints = {};
    var res_col_constraints = {};
    if (cons) {
      if (cons["rsc_location"]) {
        $.each(cons["rsc_location"], function (key, value) {
          loc_con[value["id"]] = value;
        });
      }
      if (cons["rsc_order"]) {
        $.each(cons["rsc_order"], function (key, value) {
          if (value["sets"]) {
            ord_set_con[value["id"]] = value;
          }
          else {
            ord_con[value["id"]] = value;
          }
        });
      }
      if (cons["rsc_colocation"]) {
        $.each(cons["rsc_colocation"], function (key, value) {
          col_con[value["id"]] = value;
        });
      }
    }

    $.each(loc_con, function (key, value) {
      res_loc_constraints[value["rsc"]] = res_loc_constraints[value["rsc"]] || [];
      res_loc_constraints[value["rsc"]].push(value);
    });
    $.each(ord_con, function (key, value) {
      first = $.extend({"other_rsc":value["then"],"before":false}, value);
      if (value["first"] in res_ord_constraints)
        res_ord_constraints[value["first"]].push(first);
      else res_ord_constraints[value["first"]] = [first];
      then = $.extend({"other_rsc":value["first"],"before":true}, value);
      if (value["then"] in res_ord_constraints)
        res_ord_constraints[value["then"]].push(then);
      else res_ord_constraints[value["then"]] = [then];
    });

    $.each(ord_set_con, function(key, set_con) {
      $.each(set_con["sets"], function(key, set) {
        $.each(set["resources"], function(key, resource) {
          res_ord_set_constraints[resource] = res_ord_set_constraints[resource] || [];
          if (res_ord_set_constraints[resource].indexOf(set_con) != -1) {
            return;
          }
          res_ord_set_constraints[resource].push(set_con);
        })
      })
    });

    $.each(col_con, function (key, value) {
      if (value["score"] == "INFINITY")
        value["together"] = "Together";
      else if (value["score"] == "-INFINITY" || value["score"] < 0)
        value["together"] = "Apart";
      else if (value["score"] >= 0)
        value["together"] = "Together";

      first = $.extend({"other_rsc":value["with-rsc"],"first":true}, value);
      if (value["rsc"] in res_col_constraints)
        res_col_constraints[value["rsc"]].push(first);
      else res_col_constraints[value["rsc"]] = [first];
      second = $.extend({"other_rsc":value["rsc"],"first":false}, value);
      if (value["with-rsc"] in res_col_constraints)
        res_col_constraints[value["with-rsc"]].push(second);
      else res_col_constraints[value["with-rsc"]] = [second];
    });
    return {
      "location_constraints": res_loc_constraints,
      "ordering_constraints": res_ord_constraints,
      "ordering_set_constraints": res_ord_set_constraints,
      "colocation_constraints": res_col_constraints
    };
  },

  remove_constraint: function(constraint_id) {
    $.each(this.get('resource_map'), function(key, resource) {
      $.each(
        [
          "location_constraints",
          "ordering_constraints",
          "ordering_set_constraints",
          "colocation_constraints"
        ],
        function(_, constraint_type) {
          if (resource.get(constraint_type)) {
            resource.set(
              constraint_type,
              $.grep(
                resource.get(constraint_type),
                function(value2, key) { return value2.id != constraint_id; }
              )
            );
          }
        }
      );
    });
  },

  update_meta_attr: function(resource_id, attr, value) {
    value = typeof value !== 'undefined' ? value.trim() : "";
    var data = {
      res_id: resource_id,
      key: attr,
      value: value
    };

    $.ajax({
      type: 'POST',
      url: get_cluster_remote_url() + 'add_meta_attr_remote',
      data: data,
      timeout: pcs_timeout,
      error: function (xhr, status, error) {
        alert("Unable to update meta attribute '" + attr + "': ("+error+")");
      },
      complete: function() {
        Pcs.update();
      }
    });
  },

  enable_resource: function(resource_id) {
    $.ajax({
      type: 'POST',
      url: get_cluster_remote_url() + 'resource_start',
      data: {resource: resource_id},
      timeout: pcs_timeout,
      success: function(data) {
        if (data['error']) {
          alert("Unable to enable resource '" + resource_id + "': (" + data['stderr'] + ")");
        }
      },
      error: function(xhr, status, error) {
        alert("Unable to enable resource '" + resource_id + "': (" + error + ")");
      },
      complete: function() {
        Pcs.update();
      }
    });
  },

  disable_resource: function(resource_id) {
    $.ajax({
      type: 'POST',
      url: get_cluster_remote_url() + 'resource_stop',
      data: {resource: resource_id},
      timeout: pcs_timeout,
      success: function(data) {
        if (data['error']) {
          alert("Unable to disable resource '" + resource_id + "': (" + data['stderr'] + ")");
        }
      },
      error: function(xhr, status, error) {
        alert("Unable to disable resource '" + resource_id + "': (" + error + ")");
      },
      complete: function() {
        Pcs.update();
      }
    });
  },

  delete_resources: function(type, resource_list) {
    var self = this;
    var list = self.get(type);
    $.each(resource_list, function(i, resource) {
      list.removeObject(resource);
    });
  },

  delete_unused_resources: function(type, used_map) {
    var self = this;
    var to_delete = [];
    var list = self.get(type);
    $.each(list, function(i, resource) {
      if (!(resource.get('id') in used_map)) {
        to_delete.push(resource);
      }
    });
    self.delete_resources(type, to_delete);
  },

  update: function(data) {
    var self = this;
    self.set('group_list', data['groups']);
    var resources = data["resource_list"];
    var resource_obj = null;
    var resource_id;
    var new_resource_map = {};
    var top_resource_map = {};
    $.each(resources, function(index, resource) {
      var update = false;
      resource_id = resource.id;
      if (resource_id in self.get('top_level_resource_map')) {
        resource_obj = self.get('top_level_resource_map')[resource_id];
        resource_obj.update(resource_obj, resource);
        update = true;
      } else {
        switch (resource["class_type"]) {
          case "primitive":
            resource_obj = Pcs.PrimitiveObj.create(resource);
            break;
          case "group":
            resource_obj = Pcs.GroupObj.create(resource);
            break;
          case "clone":
            resource_obj = Pcs.CloneObj.create(resource);
            break;
          case "master":
            resource_obj = Pcs.MasterSlaveObj.create(resource);
            break;
        }
      }

      top_resource_map[resource_obj.get('id')] = resource_obj;
      $.each(self.get_family_list(resource_obj), function(index, resource) {
        new_resource_map[resource.get('id')] = resource;
      });

      if (!update) {
        console.log('adding to list');
        if (resource_obj.stonith) {
          self.get('fence_list').pushObject(resource_obj);
        } else {
          self.get('resource_list').pushObject(resource_obj);
        }
      }
    });

    self.set('top_level_resource_map', top_resource_map);
    self.set('resource_map', new_resource_map);

    self.delete_unused_resources("fence_list", top_resource_map);
    self.delete_unused_resources("resource_list", top_resource_map);

    var constraints = self.get_constraints(data["constraints"]);
    self.set('constraints', constraints);
    var resource_map = self.get('resource_map');
    $.each(constraints, function(const_type, cons) {
      $.each(cons, function(resource_id, cons_list) {
        if (resource_id in resource_map)
          resource_map[resource_id].set(const_type, cons_list);
      });
    });
  }
});

Pcs.ResourceObj = Ember.Object.extend({
  id: null,
  _id: Ember.computed.alias('id'),
  name: Ember.computed.alias('id'),
  parent: null,
  meta_attr: [],
  meta_attributes: Ember.computed.alias('meta_attr'),
  disabled: false,
  error_list: [],
  warning_list: [],
  get_group_id: function() {
    var self = this;
    var p = self.get('parent');
    if (p && p.get('class_type') == 'group') {
      return p.get('id');
    }
    return null;
  }.property('parent'),
  group_selector: function() {
    var self = this;
    var cur_group = self.get('get_group_id');
    var html = '<select>\n<option value="">None</option>\n';
    $.each(Pcs.resourcesContainer.get('group_list'), function(_, group) {
      html += '<option value="' + group + '"';
      if (cur_group === group) {
        html += 'selected';
      }
      html += '>' + group + '</option>\n';
    });
    html += '</select><input type="button" value="Change group" onclick="resource_change_group(curResource(), $(this).prev().prop(\'value\'));">';
    return html;
  }.property('Pcs.resourceContainer.group_list', 'get_group_id'),
  status: "unknown",
  class_type: null, // property to determine type of the resource
  resource_type: function() { // this property is just for displaying resource type in GUI
    var t = this.get("class_type");
    return t[0].toUpperCase() + t.slice(1);
  }.property("class_type"),
  res_type: Ember.computed.alias('resource_type'),
  status_icon: function() {
    var icon_class;
    switch (this.get('status')) {
      case "running":
        icon_class = "check";
        break;
      case "disabled":
      case "partially running":
        icon_class = "warning";
        break;
      case "failed":
      case "blocked":
        icon_class = "error";
        break;
      default:
        icon_class = "x";
    }
    return "<div style=\"float:left;margin-right:6px;height:16px;\" class=\"" + icon_class + " sprites\"></div>";
  }.property("status_val"),
  status_val: function() {
    if (this.get('warning_list').length)
      return get_status_value("warning");
    if (this.get('error_list').length)
      return get_status_value("error");
    return get_status_value(this.status);
  }.property('status', 'error_list.@each.message', 'warning_list.@each.message'),
  status_color: function() {
    return get_status_color(this.get("status_val"));
  }.property("status_val"),
  status_style: function() {
    var color = get_status_color(this.get("status_val"));
    return "color: " + color + ((color != "green")? "; font-weight: bold;" : "");
  }.property("status_val"),
  show_status: function() {
    return '<span style="' + this.get('status_style') + '">' + this.get('status') + '</span>';
  }.property("status_style", "disabled"),
  status_class: function() {
    var show = ((Pcs.clusterController.get("show_all_resources"))? "" : "hidden ");
    return ((this.get("status_val") == get_status_value("ok") || this.status == "disabled") ? show + "default-hidden" : "");
  }.property("status_val"),
  status_class_fence: function() {
    var show = ((Pcs.clusterController.get("show_all_fence"))? "" : "hidden ");
    return ((this.get("status_val") == get_status_value("ok")) ? show + "default-hidden" : "");
  }.property("status", "status_val"),
  tooltip: function() {
    var self = this;
    var out = "";
    if (self.error_list.length > 0) {
      out += "<span style='color: red;  font-weight: bold;'>ERRORS:</span><br>\n";
      out += get_formated_html_list(self.error_list);
    }
    if (self.warning_list.length > 0) {
      out += "<span style='color: orange;  font-weight: bold;'>WARNINGS:</span><br>\n";
      out += get_formated_html_list(self.warning_list);
    }
    return out;
  }.property("error_list.@each", "warning_list.@each"),

  location_constraints: [],
  ordering_constraints: [],
  ordering_set_constraints: [],
  colocation_constraints: [],

  get_map: function() {
    var self = this;
    var map = {};
    map[self.get('id')] = self;
    return map;
  },

  get_full_warning_list: function() {
    var self = this;
    var warning_list = [];
    $.each(self.get_map(), function(name, resource){
      warning_list = warning_list.concat(resource.get('warning_list'));
    });
    return warning_list;
  },

  get_full_error_list: function() {
    var self = this;
    var error_list = [];
    $.each(self.get_map(), function(name, resource){
      error_list = error_list.concat(resource.get('error_list'));
    });
    return error_list;
  },

  update: function(self, data) {
    $.each(data, function(k, v) {
      self.set(k, v);
    });
    self.refresh();
  }
});

Pcs.ResourceStatusObj = Ember.Object.extend({
  id: null,
  resource_agent: null,
  managed: false,
  failed: false,
  role: null,
  active: false,
  orphaned: false,
  failure_ignored: false,
  nodes_running_on: 0,
  pending: null,
  node: null
});

Pcs.ResourceOperationObj = Ember.Object.extend({
  call_id: 0,
  crm_debug_origin: null,
  crm_feature_set: null,
  exec_time: 0,
  exit_reason: null,
  id: null,
  interval: 0,
  last_rc_change: 0,
  last_run: 0,
  on_node: null,
  op_digest: null,
  operation: null,
  operation_key: null,
  op_force_restart: null,
  op_restart_digest: null,
  op_status: 0,
  queue_time: 0,
  rc_code: 0,
  transition_key: null,
  transition_magic: null
});

Pcs.PrimitiveObj = Pcs.ResourceObj.extend({
  agentname: null,
  provider: null,
  type: null,
  stonith: false,
  instance_attr: [],
  instance_status: [],
  operations: [],
  resource_type: Ember.computed.alias('agentname'),
  is_primitive: true,
  nodes_running_on: function() {
    var self = this;
    var nodes = [];
    var node = null;
    $.each(self.get('instance_status'), function(index, status) {
      node = status.get('node');
      if (node)
        nodes.push(node.name);
    });
    return nodes;
  }.property('instance_status.@each.node'),
  is_in_group: function() {
    var self = this;
    var p = self.get('parent');
    return (p && p.get('class_type') == 'group');
  }.property('parent'),
  nodes_running_on_string: function() {
    return this.get('nodes_running_on').join(', ');
  }.property('nodes_running_on'),

  refresh: function() {
    var self = this;
    var stat = self.get("crm_status");
    var new_stat = [];
    $.each(stat, function(i,v) {
      new_stat.push(Pcs.ResourceStatusObj.create(v));
    });
    var ops = self.get("operations");
    var new_ops = [];
    $.each(ops, function(i,v) {
      new_ops.push(Pcs.ResourceOperationObj.create(v));
    });
    self.set("instance_status", new_stat);
    self.set("operations", new_ops);
    self.set("crm_status", null);
  },

  init: function() {
    this.refresh();
  }
});

Pcs.GroupObj = Pcs.ResourceObj.extend({
  members: [],
  is_group: true,
  children: Ember.computed.alias('members'),

  init: function() {
    this.refresh();
  },

  get_map: function() {
    var self = this;
    var map = self._super();
    var members = self.get('members');
    $.each(members, function(i, m){
      $.extend(map, m.get_map());
    });
    return map;
  },

  refresh: function() {
    var self = this;
    var members = self.get("members");
    var member;
    var new_members = [];
    $.each(members, function(i,v) {
      member = Pcs.PrimitiveObj.create(v);
      member.set('parent', self);
      new_members.push(member);
    });
    self.set("members", new_members);
  }
});

Pcs.MultiInstanceObj = Pcs.ResourceObj.extend({
  member: null,
  children: function() {
    return [this.get('member')];
  }.property('member'),
  unique: false,
  managed: false,
  failed: false,
  failure_ignored: false,
  is_multi_instance: true,

  get_map: function() {
    var self = this;
    var map = self._super();
    $.extend(map, self.get('member').get_map());
    return map;
  },

  init: function() {
    this.refresh();
  },

  refresh: function() {
    var self = this;
    var member = self.get("member");
    var new_member = null;
    switch (member.class_type) {
      case "primitive":
        new_member = Pcs.PrimitiveObj.create(member);
        break;
      case "group":
        new_member = Pcs.GroupObj.create(member);
    }
    new_member.set('parent', self);
    self.set("member", new_member);
  }
});

Pcs.CloneObj = Pcs.MultiInstanceObj.extend({
  is_clone: true
});

Pcs.MasterSlaveObj = Pcs.MultiInstanceObj.extend({
  masters: [],
  slaves: [],
  resource_type: 'Master/Slave'
});

Pcs.Router.map(function() {
  this.route("Configuration", { path: "configure"});

  this.resource("ACLs", {path: "acls/:aclrole_id"}, function () {
    this.route("new");
  });
  this.route("ACLs", {path: "acls"});

  this.resource("Fence Devices", {path: "fencedevices/:stonith_id"}, function () {
    this.route('new');
  });
  this.route("Fence Devices", { path: "fencedevices"});

  this.resource("Resources", {path: "resources/:resource_id"}, function () {
    this.route('new');
  });
  this.route("Resources", { path: "resources"});

  this.resource("Nodes", {path: "nodes/:node_id"}, function () {
    this.route('new');
  });
  this.route("Nodes", { path: "nodes"});

//  this.resource("Resource", {path: 'resources/:resource_id'});
  this.route("Manage", {path: "manage"});
  this.route("Wizards", {path: "wizards"});
  this.route("Default Route", { path: "*x" });
});

Pcs.ManageRoute = Ember.Route.extend({
  setupController: function(controller, model) {
    select_menu("MANAGE");
  }
});

Pcs.WizardsRoute = Ember.Route.extend({
  setupController: function(controller, model) {
    select_menu("WIZARDS");
  }
});

Pcs.IndexRoute = Ember.Route.extend({
  setupController: function(controller, model) {
    if (window.location.pathname == "/manage" || window.location.pathname == "/manage/")
      select_menu("MANAGE");
    else
      select_menu("NODES");
  }
});

Pcs.DefaultRouteRoute = Ember.Route.extend({
  setupController: function(controller, model) {
    if (window.location.pathname.substring(0,7) == "/manage")
      select_menu("MANAGE");
    else
      select_menu("NODES");
  }
});

Pcs.FenceDevicesRoute = Ember.Route.extend({
  setupController: function(controller, model) {
    select_menu("FENCE DEVICES");
  },
  model: function(params) {
    Ember.debug("Router FD: " + params.stonith_id);
    Pcs.opening_resource = params.stonith_id;
    return null;
  }
});

Pcs.NodesRoute = Ember.Route.extend({
  setupController: function(controller, model) {
    select_menu("NODES");
  },
  model: function(params) {
    Pcs.opening_node = params.node_id;
    return null;
  }
});

Pcs.ACLsRoute = Ember.Route.extend({
  setupController: function(controller, model) {
    select_menu("ACLS");
  },
  model: function(params) {
    Pcs.opening_aclrole = params.aclrole_id;
    return null;
  }
});

Pcs.ConfigurationRoute = Ember.Route.extend({
  setupController: function(controller, model) {
    select_menu("CONFIGURE"); 
  }
});

Pcs.ResourcesRoute = Ember.Route.extend({
  setupController: function(controller, model) {
    if (model) {
      select_menu("RESOURCES",model.name);
    } else {
      select_menu("RESOURCES"); 
    }
  },
  model: function(params) {
    Pcs.resourcesContainer.set('resource_id_to_load', params.resource_id);
    return params.resource_id;
  }
});

Pcs.Setting = Ember.Object.extend({
  name: null,
  value: null,
  type: null
});

Pcs.Clusternode = Ember.Object.extend({
  name: null,
  status: null,
  status_val: function() {
    if (this.warnings && this.warnings.length)
      return get_status_value("warning");
    if (this.errors && this.errors.length)
      return get_status_value("error");
    return get_status_value(this.status);
  }.property("status"),
  status_style: function() {
    var color = get_status_color(this.get("status_val"));
    return "color: " + color + ((color != "green")? "; font-weight: bold;" : "");
  }.property("status_val"),
  status_class: function() {
    var show = ((Pcs.clusterController.get("show_all_nodes"))? "" : "hidden ");
    return ((this.get("status_val") == get_status_value("ok") || this.status == "standby") ? show + "default-hidden" : "");
  }.property("status_val"),
  status_icon: function() {
    var icon_class = {"-1": "x", 1: "error", 2: "warning", 3: "x", 4: "check"};
    return "<div style=\"float:left;margin-right:6px;\" class=\"" + icon_class[this.get("status_val")] + " sprites\"></div>";
  }.property("status_val"),
  error_list: [],
  warning_list: [],
  tooltip: function() {
    var self = this;
    var out = "";
    if (self.error_list && self.error_list.length > 0) {
      out += "<span style='color: red;  font-weight: bold;'>ERRORS:</span><br>\n";
      out += get_formated_html_list(self.error_list);
    }
    if (self.warning_list && self.warning_list.length > 0) {
      out += "<span style='color: orange;  font-weight: bold;'>WARNINGS:</span><br>\n";
      out += get_formated_html_list(self.warning_list);
    }
    return out;
  }.property("error_list", "warning_list"),
  quorum: null,
  quorum_show: function() {
    if (this.status == "unknown" || this.status == "offline" || this.get('quorum') === null) {
      return '<span style="color: orange; font-weight: bold;">unknown</span>';
    } else if (this.quorum) {
      return '<span style="color: green;">YES</span>';
    } else {
      return '<span style="color: red; font-weight: bold;">NO</span>';
    }
  }.property("status", "quorum"),
  cur_node: false,
  checked: false,
  resources_running: [],
  url: function() { return "window.location='/nodes/" + this.get("name")+"'"
  }.property(),
  trclass: function(){
    if (this.cur_node == true)
      return "node_selected";
  }.property("cur_node"),
  onmouseover: function(){
    if (this.cur_node == true)
      return ""
    else
      return "hover_over(this);"
  }.property("cur_node"),
  onmouseout: function(){
    if (this.cur_node == true)
      return ""
    else
      return "hover_out(this);"
  }.property("cur_node"),
  showArrow: function(){
    if (this.cur_node != true)
      return "display:none;"
    else
      return ""
  }.property("cur_node"),
  node_name_style: function() {
    if (this.up) {
      return "";
    } else {
      if (this.pacemaker_standby)
      	return "color: #ff6600";
      else
	return "color:red";
    }
  }.property("up","pacemaker_standby"),
  standby_style: function () {
    if (this.pacemaker_standby)
      return "display: none;";
    else
      return "";
  }.property("pacemaker_standby"),
  unstandby_style: function() {
    if (this.pacemaker_standby)
      return "";
    else
      return "display: none;";
  }.property("pacemaker_standby"),
  corosync_startup: function() {
    if (this.corosync_enabled)
      return "Enabled";
    else
      return "Disabled";
  }.property("corosync_enabled"),
  pacemaker_startup: function() {
    if (this.pacemaker_enabled)
      return "Enabled";
    else
      return "Disabled";
  }.property("pacemaker_enabled"),
  pcsd_startup: function() {
    if (this.pcsd_enabled)
      return "Enabled";
    else
      return "Disabled";
  }.property("pcsd_enabled"),
  location_constraints: null
});

Pcs.Aclrole = Ember.Object.extend({
  name: null,
  cur_role: false,
  checked: false,
  description: "",
  user_list: null,
  group_list: null,
  trclass: function() {
    return this.cur_role ? "node_selected" : "";
  }.property("cur_role"),
  onmouseover: function() {
    return this.cur_role ? "" : "hover_over(this);"
  }.property("cur_role"),
  onmouseout: function() {
    return this.cur_role ? "" : "hover_out(this);"
  }.property("cur_role"),
  showArrow: function(){
    return this.cur_role ? "" : "display:none";
  }.property("cur_role"),
});

Pcs.Cluster = Ember.Object.extend({
  name: null,
  url_link: function(){return get_cluster_remote_url(this.name) + "main";}.property("name"),
  input_name: function(){return "clusterid-" + this.name;}.property("name"),
  div_id: function(){return "cluster_info_" + this.name}.property("name"),
  status: "unknown",
  status_unknown: function() {
    return this.status == "unknown";
  }.property("status"),
  status_icon: function() {
    var icon_class = {"-1": "x", 1: "error", 2: "warning", 3: "x", 4: "check"};
    return "<div style=\"float:left;margin-right:6px;\" class=\"" + icon_class[get_status_value(this.status)] + " sprites\"></div>";
  }.property("status"),
  quorum_show: function() {
    if (this.status == "unknown") {
      return "<span style='color:orange'>(quorate unknown)</span>"
    } else if (!this.quorate) {
      return "<span style='color: red'>(doesn't have quorum)</span>"
    } else {
      return ""
    }
  }.property("status", "quorum"),
  nodes: [],
  nodes_failed: 0,
  resource_list: [],
  resources_failed: 0,
  fence_list: [],
  fence_failed: 0,
  error_list: [],
  warning_list: [],
  need_reauth: false,
  quorate: false,

  get_num_of_failed: function(type) {
    var num = 0;
    $.each(this.get(type), function(key, value) {
      if (value.get("status_val") < get_status_value("ok") && value.status != "disabled" && value.status != "standby")
        num++;
    });
    return num;
  },

  status_sort: function(a,b) {
    if (a.get("status_val") == b.get("status_val"))
      return ((a.status == b.status) ? a.get('name').localeCompare(b.get('name')) : ((a.status > b.status) ? 1 : -1));
    return status_comparator(a.status, b.status)
  },

  add_resources: function(data) {
    var self = this;
    var resources = [];
    var fence = [];
    var resource_obj;
    $.each(data, function (index, resource) {
      switch (resource["class_type"]) {
        case "primitive":
          resource_obj = Pcs.PrimitiveObj.create(resource);
          break;
        case "group":
          resource_obj = Pcs.GroupObj.create(resource);
          break;
        case "clone":
          resource_obj = Pcs.CloneObj.create(resource);
          break;
        case "master":
          resource_obj = Pcs.MasterSlaveObj.create(resource);
          break;
      }

      var url_link = get_cluster_remote_url(self.get('name')) + "main#/" +
        (resource_obj.get('stonith') ? "fencedevices/" : "resources/") +
        resource_obj.get('id');
      resource_obj.set('url_link', url_link);

      resource_obj.set('warning_list', resource_obj.get_full_warning_list());
      resource_obj.set('error_list', resource_obj.get_full_error_list());

      if (resource_obj.stonith) {
        fence.pushObject(resource_obj);
      } else {
        resources.pushObject(resource_obj);
      }
    });
    resources.sort(self.status_sort);
    fence.sort(self.status_sort);
    self.set('fence_list', fence);
    self.set('resource_list', resources);
  },

  add_nodes: function(data) {
    var self = this;
    self.set("need_reauth", false);
    var nodes = [];
    var node;
    $.each(data, function(key, val) {
      if (val["warning_list"]) {
        $.each(val["warning_list"], function (key, value) {
          if (self.get('need_reauth'))
            return false;
          if (typeof(value.type) !== 'undefined' && value.type == "nodes_not_authorized") {
            self.set("need_reauth", true);
          }
        });
      }

      node = Pcs.Clusternode.create({
        name: val["name"],
        url_link: get_cluster_remote_url(self.name) + "main#/nodes/" + val["name"],
        status: val["status"],
        quorum: val["quorum"],
        error_list: val["error_list"],
        warning_list: val["warning_list"]
      });
      nodes.push(node);
    });
    nodes.sort(self.status_sort);
    self.set("nodes", nodes);
  }
});

Pcs.clusterController = Ember.Object.create({
  cluster_list: Ember.ArrayController.create({
    content: Ember.A(), sortProperties: ['status'],
    sortAscending: true,
    sortFunction: function(a,b){return status_comparator(a,b);}
  }),
  cur_cluster: null,
  show_all_nodes: false,
  show_all_resources: false,
  show_all_fence: false,
  num_ok: 0,
  num_error: 0,
  num_warning: 0,
  num_unknown: 0,

  update_cur_cluster: function(row) {
    var self = this;
    var cluster_name = $(row).attr("nodeID");
    $("#clusters_list").find("div.arrow").hide();
    $(row).find("div.arrow").show();

    $.each(self.get('cluster_list').get('content'), function(key, cluster) {
      if (cluster.get("name") == cluster_name) {
        self.set('cur_cluster', cluster);
        return false;
      }
    });
    correct_visibility_dashboard(self.get('cur_cluster'));

    $("#node_sub_info").children().each(function (i, val) {
      if ($(val).attr("id") == ("cluster_info_" + cluster_name))
        $(val).show();
      else
        $(val).hide();
    });
  },

  update: function(data) {
    var self = this;
    var clusters = data["cluster_list"];
    var cluster_name_list = [];
    self.set("num_ok", 0);
    self.set("num_error", 0);
    self.set("num_warning", 0);
    self.set("num_unknown", 0);

    $.each(clusters, function(key, value) {
      cluster_name_list.push(value["cluster_name"]);
      var found = false;
      var cluster = null;

      $.each(self.get('cluster_list').get('content'), function(key, pre_existing_cluster) {
        if (pre_existing_cluster && pre_existing_cluster.get('name') == value["cluster_name"]) {
          found = true;
          cluster = pre_existing_cluster;
          cluster.set("status", value["status"]);
          cluster.set("quorate",value["quorate"]);
          cluster.set("error_list",value["error_list"]);
          cluster.set("warning_list",value["warning_list"]);
        }
      });

      if (!found) {
        cluster = Pcs.Cluster.create({
          name: value["cluster_name"],
          status: value["status"],
          quorate: value["quorate"],
          error_list: value["error_list"],
          warning_list: value["warning_list"]
        });
      }

      cluster.add_nodes(value["node_list"]);
      cluster.add_resources(value["resource_list"]);
      cluster.set("nodes_failed", cluster.get_num_of_failed("nodes"));
      cluster.set("resources_failed", cluster.get_num_of_failed("resource_list"));
      cluster.set("fence_failed", cluster.get_num_of_failed("fence_list"));

      if (cluster.get('status') == "ok") {
        $.each(cluster.get('fence_list').concat(cluster.get('resource_list')), function(index, res) {
          if (res.get('warning_list').length > 0) {
            cluster.set("status", "warning");
            return false;
          }
        });
      }

      switch (cluster.get('status')) {
        case "ok":
          self.incrementProperty('num_ok');
          break;
        case "error":
          self.incrementProperty('num_error');
          break;
        case "warning":
          self.incrementProperty('num_warning');
          break;
        default:
          self.incrementProperty('num_unknown');
          break;
      }

      var nodes_to_auth = [];
      $.each(cluster.get('warning_list'), function(key, val){
        if (val.hasOwnProperty("type") && val.type == "nodes_not_authorized"){
          nodes_to_auth = nodes_to_auth.concat(val['node_list']);
        }
      });
      nodes_to_auth = $.unique(nodes_to_auth);

      if (cluster.get('need_reauth') || nodes_to_auth.length > 0) {
        cluster.get('warning_list').pushObject({
          message: "There are few authentication problems. To fix them, click <a href='#' onclick='auth_nodes_dialog(" + JSON.stringify(nodes_to_auth) + ", null, function() {fix_auth_of_cluster();})'>here</a>.",
          type: "nodes_not_authorized",
          node_list: self.nodes_to_auth
        });
      }

      if (!found) {
        self.get('cluster_list').pushObject(cluster);
      }

      if (cluster.get_num_of_failed("nodes") == cluster.nodes.length) {
        if (cluster.get('status') != "unknown")
          cluster.get('warning_list').pushObject({
            message: "Cluster is offline"
          });

        cluster.set("status", "unknown");
      }
    });

    var to_remove = [];
    $.each(self.get('cluster_list').get('content'), function(key,val) {
      if (cluster_name_list.indexOf(val.get('name')) == -1) {
        to_remove.pushObject(val);
      }
    });

    $.each(to_remove, function(index, val) {
      self.get('cluster_list').removeObject(val);
    });
  }
});

Pcs.aclsController = Ember.ArrayController.createWithMixins({
  content: [],
  cur_role: null,
  role_list: function() {
    if (this.get("roles"))
      return Object.keys(this.get("roles"));
    return [];
  }.property("roles"),
  user_list: function() {
    if (this.get("users"))
      return Object.keys(this.get("users"));
    return [];
  }.property("users"),
  group_list: function() {
    if (this.get("groups"))
      return Object.keys(this.get("groups"));
    return [];
  }.property("groups"),
  load_role: function(role_row, dont_update_hash) {
    load_row(role_row, this, 'cur_role', '#role_info_div');
    if (!dont_update_hash) {
      window.location.hash = "/acls/" + $(role_row).attr("nodeID");
    }
  },
  update: function(data) {
    var self = this;
    self.set('content',[]);
    var my_groups = {}, my_users = {}, my_roles = {};
    var cur_role_holder = "";
    var cur_role_name = "";
    if (data["acls"]) {
      if (data["acls"]["group"]) {
        $.each(data["acls"]["group"], function (k2,v2) {
          my_groups[k2] = v2;
        });
      }
      if (data["acls"]["user"]) {
        $.each(data["acls"]["user"], function (k2,v2) {
          my_users[k2] = v2;
        });
      }
      if (data["acls"]["role"]) {
        $.each(data["acls"]["role"], function (k2,v2) {
          my_roles[k2] = v2;
        });
      }
    }
    self.set('roles',my_roles);
    self.set('users',my_users);
    self.set('groups',my_groups);

    cur_role_holder = self.cur_role ? self.cur_role.name : "";

    $.each(my_roles, function(role_name, role_data) {
      var found = false;
      var role = null;
      $.each(self.content, function(key, pre_existing_role) {
        if(pre_existing_role && pre_existing_role.name == role_name) {
          found = true;
          role = pre_existing_role;
          role.set("name", role_name);
          role.set("cur_role", false);
          role.set("description", role_data["description"]);
        }
      });
      if (!found) {
        role = Pcs.Aclrole.create({
          name: role_name,
          cur_role: false,
          description: role_data["description"],
        });
      }
      if (role_data["permissions"]) {
        $.each(role_data["permissions"], function(key, permission) {
          var parsed = permission.match(/(\S+)\s+(\S+)\s+(.+)\((.*)\)/);
          role["permissions"] = role["permissions"] || [];
          role["permissions"].push({
            type: parsed[1],
            xpath_id: parsed[2],
            query_id: parsed[3],
            permission_id: parsed[4],
          });
        });
      }

      if (cur_role_holder == "") {
        cur_role_name = Pcs.opening_aclrole;
      }
      else {
        cur_role_name = cur_role_holder;
      }
      if (role.name == cur_role_name) {
        role.set("cur_role", true);
        self.set("cur_role", role);
      }

      if (!found) {
        self.pushObject(role);
      }
    });

    if (self.content && self.content.length > 0 && self.cur_role == null) {
      self.set("cur_role", self.content[0]);
      self.content[0].set("cur_role", true);
    }

    $.each(my_users, function(user_name, role_list) {
      $.each(role_list, function(key1, role_name) {
        $.each(self.content, function(key2, existing_role) {
          if (existing_role.name == role_name) {
            if (!existing_role.user_list) {
              existing_role.user_list = [user_name];
            }
            else if (existing_role.user_list.indexOf(user_name) == -1) {
              existing_role.user_list.push(user_name);
            }
          }
        });
      });
    });
    $.each(my_groups, function(group_name, role_list) {
      $.each(role_list, function(key1, role_name) {
        $.each(self.content, function(key2, existing_role) {
          if (existing_role.name == role_name) {
            if (!existing_role.group_list) {
              existing_role.group_list = [group_name];
            }
            else if (existing_role.group_list.indexOf(group_name) == -1) {
              existing_role.group_list.push(group_name);
            }
          }
        });
      });
    });
  }
});

Pcs.settingsController = Ember.ArrayController.create({
  content: [],
  update: function(data) {
    var self = this;
    var settings = {};
    self.set('content',[]);
    if (data["cluster_settings"]) {
      $.each(data["cluster_settings"], function(k2, v2) {
        var setting = Pcs.Setting.create({
          name: k2,
          value: v2
        });
        self.pushObject(setting);
      });
    }
  }
});

Pcs.selectedNodeController = Ember.Object.createWithMixins({
  node: null,
  reset: function() {
    if (Pcs.nodesController)
      this.set('node', Pcs.nodesController.objectAt(0));
  }
});

Pcs.nodesController = Ember.ArrayController.createWithMixins({
  content: [],
  cur_node: null,
  cur_node_attr: function () {
    var ret_val = [];
    var nc = this;
    $.each(this.content, function(node, value) {
      if ("node_attrs" in value && nc.cur_node && value["node_attrs"]) {
        if (nc.cur_node.name in value["node_attrs"]) {
          ret_val = ret_val.concat(value["node_attrs"][nc.cur_node.name]);
        }
        return false;
      }
    });
    return ret_val;
  }.property("cur_node", "content.@each.node_attrs"),
  cur_node_fence_levels: function () {
    var ret_val = [];
    var nc = this;
    $.each(this.content, function(node, value) {
      if ("fence_levels" in value && nc.cur_node && value["fence_levels"]) {
        if (nc.cur_node.name in value["fence_levels"]) {
          ret_val = ret_val.concat(value["fence_levels"][nc.cur_node.name]);
        }
        return false;
      }
    });
    return ret_val;
  }.property("cur_node", "content.@each.fence_levels"),
  init: function(){
    this._super();
  },

  load_node: function(node_row, dont_update_hash){
    load_row(node_row, this, 'cur_node', '#node_info_div');
    if (!dont_update_hash)
      window.location.hash = "/nodes/" + $(node_row).attr("nodeID");
  },

  update: function(data){
    var self = this;
    var nodes = [];
    var corosync_nodes_online = data["corosync_online"];
    var pacemaker_nodes_online = data["pacemaker_online"];
    var pacemaker_nodes_standby = data["pacemaker_standby"];

    var resources_on_nodes = {};
    var lc_on_nodes = {};
    $.each(data['node_list'], function(index, node) {
      nodes.push(node.name);

      resources_on_nodes[node.name] = [];
      $.each(Pcs.resourcesContainer.get('resource_map'), function(resource_id, resource_obj) {
        var nodes_running_on = resource_obj.get('nodes_running_on');
        if (nodes_running_on) {
          $.each(nodes_running_on, function(index, node_name) {
            if (node.name == node_name) {
              resources_on_nodes[node.name].push(resource_id);
            }
          });
        }
      });

      lc_on_nodes[node.name] = [];
      if (data["constraints"] && data["constraints"]["rsc_location"]) {
        $.each(data["constraints"]["rsc_location"], function(key, constraint) {
          if (constraint["node"] == node.name)
            lc_on_nodes[node.name].push(constraint)
        });
      }
    });

    var nodes_checked = {};
    var cur_node_holder = "";
    if (self.cur_node)
      cur_node_holder = self.cur_node.name;
    $.each(self.content, function (key, value) {
      if (value.checked)
        nodes_checked[value.name] = true;
    });

    $.each(data['node_list'], function(_, node_obj) {
      var node_id = node_obj.name;
      if ($.inArray(node_id, corosync_nodes_online) > -1) {
        corosync_online = true;
      } else {
        corosync_online = false;
      }

      if ($.inArray(node_id, pacemaker_nodes_online) > -1) {
        pacemaker_online = true;
      } else {
        pacemaker_online = false;
      }

      if ($.inArray(node_id, pacemaker_nodes_standby) > -1) {
        pacemaker_standby = true;
      } else {
        pacemaker_standby = false;
      }

      if (node_obj["noresponse"] == true) {
        pcsd_daemon = false
      } else {
        pcsd_daemon = true
      }

      if (node_obj["notauthorized"] == "true" || node_obj["notoken"] == true) {
        authorized = false;
      } else {
        authorized = true;
      }

      if (node_obj["corosync"] && node_obj["pacemaker"] &&
        pacemaker_online && corosync_online) {
        up_status = true;
      } else {
        up_status = false;
      }

      var node_attr = {};
      if (node_obj["attr"]) {
        $.each(node_obj["attr"], function(_, attr) {
          node_attr[attr.name] = attr.value;
        });
      }

      found = false;
      var node = null;
      $.each(self.content, function(key, pre_existing_node) {
        if (pre_existing_node && pre_existing_node.name == node_id) {
          node = pre_existing_node;
          found = true;
          node.set("authorized",authorized);
          node.set("up",up_status);
          node.set("pcsd",pcsd_daemon && authorized);
          node.set("corosync_daemon", node_obj["corosync"]);
          node.set("corosync_enabled", node_obj["corosync_enabled"]);
          node.set("pacemaker_daemon", node_obj["pacemaker"]);
          node.set("pacemaker_enabled", node_obj["pacemaker_enabled"]);
          node.set("pcsd_enabled", node_obj["pcsd_enabled"]);
          node.set("corosync", corosync_online);
          node.set("pacemaker", pacemaker_online);
          node.set("pacemaker_standby", pacemaker_standby);
          node.set("cur_node",false);
          node.set("running_resources", Pcs.getResourcesFromID($.unique(resources_on_nodes[node_id].sort().reverse())));
          node.set("location_constraints", lc_on_nodes[node_id].sort());
          node.set("uptime", node_obj["uptime"]);
          node.set("node_id", node_obj["id"]);
          node.set("node_attrs", node_attr);
          node.set("fence_levels", node_obj["fence_levels"]);
        }
      });

      if (found == false) {
        var node = Pcs.Clusternode.create({
          name: node_id,
          authorized:  authorized,
          up: up_status,
          pcsd: pcsd_daemon && authorized,
          corosync_daemon: node_obj["corosync"],
          corosync_enabled: node_obj["corosync_enabled"],
          pacemaker_daemon: node_obj["pacemaker"],
          pacemaker_enabled: node_obj["pacemaker_enabled"],
          pcsd_enabled: node_obj["pcsd_enabled"],
          corosync: corosync_online,
          pacemaker: pacemaker_online,
          pacemaker_standby: pacemaker_standby,
          cur_node: false,
          running_resources: Pcs.getResourcesFromID($.unique(resources_on_nodes[node_id].sort().reverse())),
          location_constraints: lc_on_nodes[node_id].sort(),
          uptime: node_obj["uptime"],
          node_id: node_obj["id"],
          node_attrs: node_attr,
          fence_levels: node_obj["fence_levels"]
        });
      }
      var pathname = window.location.pathname.split('/');

      if (cur_node_holder == "") {
        cur_node_name = Pcs.opening_node;
      } else {
        cur_node_name = cur_node_holder;
      }
      if (node.name == cur_node_name) {
        node.set("cur_node",true);
        self.set("cur_node", node);
      }

      if (nodes_checked[node.name])
        node.set("checked",true);

      if (found == false)
        self.pushObject(node);
    });
    if (self.content && self.content.length > 0 && self.cur_node == null) {
      self.set("cur_node", self.content[0]);
      self.content[0].set("cur_node",true);
    }

    nodesToRemove = [];
    $.each(self.content, function (key, node) {
      found = false;
      $.each(nodes, function (k,v) {
        if (v == node.name)
          found = true;
      });
      if (!found) {
        nodesToRemove.push(node);
      }
    });

    $.each(nodesToRemove, function(k,v) {
      self.content.removeObject(v);
    });
  }
});

function myUpdate() {
  Pcs.update();
//  window.setTimeout(myUpdate,4000);
}

Pcs.update(true);
