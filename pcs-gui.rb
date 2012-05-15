require 'sinatra'
require 'sinatra/reloader' if development?
#require 'rack/ssl'
require 'open3'
require 'rexml/document'
require './resource.rb'
require './remote.rb'
require './fenceagent.rb'
require 'webrick'
require 'pp'
require 'webrick/https'
require 'openssl'

use Rack::CommonLogger
#use Rack::SSL

also_reload './resource.rb'
also_reload './remote.rb'
also_reload './fenceagent.rb'

@@cluster_name = `corosync-cmapctl totem.cluster_name`.gsub(/.*= /,"").strip
configure do
  OCF_ROOT = "/usr/lib/ocf"
  HEARTBEAT_AGENTS_DIR = "/usr/lib/ocf/resource.d/heartbeat/"
  PENGINE = "/usr/libexec/pacemaker/pengine"
  PCS = "/root/pcs/pcs/pcs" 
  CRM_ATTRIBUTE = "/usr/sbin/crm_attribute"
  COROSYNC_CONF = "/etc/corosync/corosync.conf"
end

set :port, 2222
set :logging, true

if not defined? @@cur_node_name
  @@cur_node_name = `hostname`.chomp
end

@nodes = (1..7)

helpers do
  def setup
    @nodes_online, @nodes_offline = getNodes
    @nodes = {}
    @nodes_online.each do |i|
      @nodes[i]  = Node.new(i, i, i, true)
    end
    @nodes_offline.each do |i|
      @nodes[i]  = Node.new(i, i, i, false)
    end

    if params[:node]
      @cur_node = @nodes[params[:node]]
    else
      @cur_node = @nodes.values[0]
    end

    if @nodes.length != 0
      @loc_dep_allow, @loc_dep_disallow = getLocationDeps(@cur_node)
    end
  end

  def getParamLine(params)
    param_line = ""
    params.each { |param, val|
      if param.start_with?("_res_param_")
	myparam = param.sub(/^_res_param_/,"")
	param_line += " #{myparam}=#{val}"
      end
    }
    param_line
  end
end

post '/configure/?:page?' do
  print params
  params[:config].each { |key, value|
    if (value == "on")
      value = "true"
    elsif value == "off"
      value = "false"
    end

    print `#{CRM_ATTRIBUTE} --attr-name #{key} --attr-value #{value} 2>&1`
    print "#{key} - #{value}\n"
  }
  redirect params[:splat][0]
end

post '/fencedeviceadd' do
  puts params
  param_line = getParamLine(params)
  puts "pcs stonith create #{params[:name]} #{params[:resource_type]} #{param_line}"
  puts `#{PCS} stonith create #{params[:name]} #{params[:resource_type]} #{param_line}`
  redirect "/fencedevices/#{params[:name]}"
end

post '/resourceadd' do
  param_line = getParamLine(params)
  puts "pcs resource create #{params[:name]} #{params[:resource_type]} #{param_line}"
  puts `#{PCS} resource create #{params[:name]} #{params[:resource_type]} #{param_line}`
  if params[:resource_group]
    puts "#{PCS} resource group add #{params[:resource_group]} #{params[:name]}"
    puts `#{PCS} resource group add #{params[:resource_group]} #{params[:name]}`
  end
  redirect "/resources/#{params[:name]}"
end

post '/resourcerm' do
  params.each { |k,v|
    if k.index("resid-") == 0
      puts "#{PCS} resource delete #{k.gsub("resid-","")}"
      puts `#{PCS} resource delete #{k.gsub("resid-","")}`
    end
  }
  redirect "/resources/"
end

post '/resource_group_add' do
  rg = params["resource_group"]
  resources = params["resources"]
  puts "#{PCS} resource group add #{rg} #{resources}"
  puts `#{PCS} resource group add #{rg} #{resources}`
  redirect "/resources/"
end

post '/fencerm' do
  params.each { |k,v|
    if k.index("resid-") == 0
      puts "#{PCS} resource delete #{k.gsub("resid-","")}"
      puts `#{PCS} resource delete #{k.gsub("resid-","")}`
    end
  }
  redirect "/fencedevices/"
end

get '/configure/?:page?' do
  @config_options = getConfigOptions(params[:page])
  @configuremenuclass = "class=\"active\""
  erb :configure, :layout => :main
end

get '/fencedevices/?:fencedevice?' do
  @resources, @groups = getResourcesGroups(true)
  pp @resources

  if @resources.length == 0
    @cur_resource = nil
    @resource_agents = getFenceAgents()
  else
    @cur_resource = @resources[0]
    if params[:fencedevice]
      @resources.each do |fd|
	if fd.id == params[:fencedevice]
	  @cur_resource = fd
	  @cur_resource.options = getResourceOptions(@cur_resource.id)
	  break
	end
      end
    end
    @resource_agents = getFenceAgents(@cur_resource.agentname)
  end
  erb :fencedevices, :layout => :main
end

post '/resources/:resource?' do
  pp params
  param_line = getParamLine(params)
  puts "#{PCS} resource update #{params[:resource_id]} #{param_line}"
  puts `#{PCS} resource update #{params[:resource_id]} #{param_line}`

  puts params[:resource_group]
  if params[:resource_group]
    if params[:resource_group] == ""
      if params[:_orig_resource_group] != ""
	puts "#{PCS} resource group remove_resource #{params[:_orig_resource_group]} #{params[:resource]}"
	puts `#{PCS} resource group remove_resource #{params[:_orig_resource_group]} #{params[:resource]}`
      end
    else
      puts "#{PCS} resource group add #{params[:resource_group]} #{params[:resource]}"
      puts `#{PCS} resource group add #{params[:resource_group]} #{params[:resource]}`
    end
  end
  redirect "/resources/#{params[:resource]}"
end

post '/fencedevices/:fencedevice?' do
  pp params
  param_line = getParamLine(params)
  pp param_line
  puts "#{PCS} stonith update #{params[:resource_id]} #{param_line}"
  puts `#{PCS} stonith update #{params[:resource_id]} #{param_line}`
  redirect params[:splat][0]
end

['/resources/?:resource?', '/resource_list/?:resource?'].each do |path|
  get path do
    @resources, @groups = getResourcesGroups
    @resourcemenuclass = "class=\"active\""

    if @resources.length == 0
      @cur_resource = nil
      @resource_agents = getResourceAgents()
    else
      @cur_resource = @resources[0]
      @cur_resource.options = getResourceOptions(@cur_resource.id)
      if params[:resource]
	@resources.each do |r|
	  if r.id == params[:resource]
	    @cur_resource = r
	    @cur_resource.options = getResourceOptions(r.id)
	    break
	  end
	end
      end
      @resource_agents = getResourceAgents(@cur_resource.agentname)
    end
    if path.start_with? '/resource_list'
      erb :_resource_list
    else
      erb :resource, :layout => :main
    end
  end
end

get '/resources/metadata/:resourcename/?:new?' do
  @resource = ResourceAgent.new(params[:resourcename])
  @resource.required_options, @resource.optional_options = getResourceMetadata(HEARTBEAT_AGENTS_DIR + params[:resourcename])
  @new_resource = params[:new]
  @resources, @groups = getResourcesGroups
  
  erb :resourceagentform
end

get '/fencedevices/metadata/:fencedevicename/?:new?' do
  @fenceagent = FenceAgent.new(params[:fencedevicename])
  @fenceagent.required_options, @fenceagent.optional_options = getFenceAgentMetadata(params[:fencedevicename])
  @new_fenceagent = params[:new]
  
  erb :fenceagentform
end

get '/nodes/?:node?' do
  setup()
  @nodemenuclass = "class=\"active\""
  @resources, @groups = getResourcesGroups
  @resources_running = []
  @resources.each { |r|
    @cur_node && r.nodes && r.nodes.each {|n|
      if n.name == @cur_node.id
	@resources_running << r
      end
    }
  }
  erb :nodes, :layout => :main
end

get '/' do
  print "Redirecting...\n"
  call(env.merge("PATH_INFO" => '/nodes'))
end

get '/remote/?:command?' do
  return remote(params)
end

post '/remote/?:command?' do
  return remote(params)
end

get '*' do
  print params[:splat]
  print "2Redirecting...\n"
  call(env.merge("PATH_INFO" => '/nodes'))
end

def getLocationDeps(cur_node)
  stdin, stdout, stderror = Open3.popen3("#{PCS} constraint location show nodes #{cur_node.id}")
  out = stdout.readlines
  deps_allow = []
  deps_disallow = []
  allowed = false
  disallowed = false
  out.each {|line|
    line = line.strip
    next if line == "Location Constraints:" or line.match(/^Node:/)

    if line == "Allowed to run:"
      allowed = true
      next
    elsif line == "Not allowed to run:"
      disallowed = true
      next
    end

    if disallowed == true
      deps_disallow << line.sub(/ .*/,"")
    elsif allowed == true
      deps_allow << line.sub(/ .*/,"")
    end
  }  
  [deps_allow, deps_disallow]
end

# Return array containing an array of nodes online & nodes offline
# [ Nodes Online, Nodes Offline] 
def getNodes
  stdin, stdout, stderror, waitth = Open3.popen3("#{PCS} status nodes")
  out = stdout.readlines

  online = out[1]
  offline = out[2]

  if online
    online = online.split(' ')[1..-1].sort
  else
    online = []
  end

  if offline
    offline = offline.split(' ')[1..-1].sort
  else
    offline = []
  end

  # If exit status is 0, then the cluster probably isn't running so we use
  # corosync node list
  if waitth.value.exitstatus != 0
    stdin, stdout, stderror, waitth = Open3.popen3("#{PCS} status nodes corosync")
    out = stdout.readlines
    if out.length > 0
      out2 = out[0].chomp.split(/: /)
      if out2.length > 1
	out2[1].split(/ /).each {|n| 
	  offline << n
	}
	return [[],offline]
      end
    end

    return [[],[]]
  end
  [online, offline]
end


def getConfigOptions(page="general")
  config_options = []
  case page
  when "general", nil
    cg1 = []
    cg1 << ConfigOption.new("Cluster Delay Time", "cdt",  "int", 4, "Seconds") 
    cg1 << ConfigOption.new("Batch Limit", "cdt",  "int", 4) 
    cg1 << ConfigOption.new("Default Action Timeout", "cdt",  "int", 4, "Seconds") 
    cg2 = []
    cg2 << ConfigOption.new("During timeout should cluster stop all active resources", "res_stop", "radio", "4", "", ["Yes","No"])

    cg3 = []
    cg3 << ConfigOption.new("PE Error Storage", "res_stop", "radio", "4", "", ["Yes","No"])
    cg3 << ConfigOption.new("PE Warning Storage", "res_stop", "radio", "4", "", ["Yes","No"])
    cg3 << ConfigOption.new("PE Input Storage", "res_stop", "radio", "4", "", ["Yes","No"])

    config_options << cg1
    config_options << cg2
    config_options << cg3
  when "pacemaker"
    cg1 = []
    cg1 << ConfigOption.new("Batch Limit", "batch-limit",  "int", 4, "jobs") 
    cg1 << ConfigOption.new("No Quorum Policy", "no-quorum-policy",  "dropdown","" ,"", {"ignore" => "Ignore","freeze" => "Freeze", "stop" => "Stop", "suicide" => "Suicide"}) 
    cg1 << ConfigOption.new("Symmetric", "symmetric-cluster", "check")
    cg2 = []
    cg2 << ConfigOption.new("Stonith Enabled", "stonith-enabled", "check")
    cg2 << ConfigOption.new("Stonith Action", "stonith-action",  "dropdown","" ,"", {"reboot" => "Reboot","poweroff" => "Poweroff"}) 
    cg3 = []
    cg3 << ConfigOption.new("Cluster Delay", "cluster-delay",  "int", 4) 
    cg3 << ConfigOption.new("Stop Orphan Resources", "stop-orphan-resources", "check")
    cg3 << ConfigOption.new("Stop Orphan Actions", "stop-orphan-actions", "check")
    cg3 << ConfigOption.new("Start Failure is Fatal", "start-failure-is-fatal", "check")
    cg3 << ConfigOption.new("PE Error Storage", "pe-error-series-max", "int", "4")
    cg3 << ConfigOption.new("PE Warning Storage", "pe-warn-series-max", "int", "4")
    cg3 << ConfigOption.new("PE Input Storage", "pe-input-series-max", "int", "4")

    config_options << cg1
    config_options << cg2
    config_options << cg3
  end

  allconfigoptions = []
  config_options.each { |i| i.each { |j| allconfigoptions << j } }
  ConfigOption.getDefaultValues(allconfigoptions)
  return config_options
end

class Node
  attr_accessor :active, :id, :name, :hostname

  def initialize(id=nil, name=nil, hostname=nil, active=nil)
    @id, @name, @hostname, @active = id, name, hostname, active
  end
end


class ConfigOption
  attr_accessor :name, :configname, :type, :size, :units, :options, :default
  def initialize(name, configname, type="str", size = 10, units = "", options = [])
    @name = name
    @configname = configname
    @type = type
    @size = size
    @units = units
    @options = options
  end

  def value
    @@cache_value ||= {}
    @@cache_value = {}
    if @@cache_value[configname]  == nil
      resource_options = `#{CRM_ATTRIBUTE} --get-value -n #{configname} 2>&1`
      resource_value = resource_options.sub(/.*value=/m,"").strip
      if resource_value == "(null)"
	@@cache_value[configname] = default
      else
	@@cache_value[configname] = resource_value
      end
    else
      print "#{configname} is defined: #{@@cache_value[configname]}...\n"
    end

    return @@cache_value[configname]
  end

  def self.getDefaultValues(cos)
    metadata = `#{PENGINE} metadata`
    doc = REXML::Document.new(metadata)

    cos.each { |co|
      puts "resource-agent/parameters/parameter[@name='#{co.configname}']"
      doc.elements.each("resource-agent/parameters/parameter[@name='#{co.configname}']/content") { |e|
	co.default = e.attributes["default"]
	break
      }
    }
  end

  def checked(option)
    case type
    when "radio"
      val = value
      if option == "Yes"
	if val == "true"
	  return "checked"
	end
      else
	if val == "false"
	  return "checked"
	end
      end
    when "check"
      if value == "true"
	return "checked"
      end
    when "dropdown"
      print "Dropdown: #{value}-#{option}\n"
      if value == option
	return "selected"
      end
    end
  end

  def html
    paramname = "config[#{configname}]"
    case type
    when "int"
      return "<input name=\"#{paramname}\" value=\"#{value}\" type=text size=#{size}>"
    when "str"
      return "<input name=\"#{paramname}\" value=\"#{value}\" type=text size=#{size}>"
    when "radio"
      ret = ""
      options.each {|option|
	ret += "<input type=radio #{checked(option)} name=\"#{paramname}\" value=\"#{option}\">#{option}"
      }
      return ret
    when "check"
      ret = "<input name=\"#{paramname}\" value=\"off\" type=hidden size=#{size}>"
      ret += "<input name=\"#{paramname}\" #{checked(paramname)} type=checkbox size=#{size}>"
      return ret
    when "dropdown"
      ret = "<select name=\"#{paramname}\">"
      options.each {|key, option|
	ret += "<option #{checked(key)} value=\"#{key}\">#{option}</option>"
      }
      ret += "<select"
      return ret
    end
  end
end
