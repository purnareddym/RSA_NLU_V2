#----------------------- load common defs ---------------------------------#
execfile('<%= @download_dir %>/<%= @domain_name %>/utils.py')
#------------------------ LOAD VARIABLES ----------------------------------#
MW_HOME = '<%= @middleware_home_dir %>'
WEBLOGIC_VERSION = '<%= @weblogic_version %>'
DOMAIN_PATH = '<%= @domains_dir %>'
DOMAIN = '<%= @domain_name %>'
DEVELOPMENT_MODE = false
JAVA_HOME = '<%= @java_home %>'
JSSE_ENABLED = true

ADMIN_SERVER = '<%= @admin_server %>'
ADMIN_USER = '<%= @admin_user %>'
ADMIN_PASSWORD = '<%= @admin_password %>'
ADMIN_SERVER_LISTEN_ADDRESS = '<%= @admin_server_listen_address %>'
ADMIN_SERVER_LISTEN_PORT = '<%= @admin_server_port %>'
ADMIN_SERVER_SSL_PORT = int(ADMIN_SERVER_LISTEN_PORT) + 1
MACHINE = ADMIN_SERVER_LISTEN_ADDRESS.split('.')
ADMIN_MACHINE = MACHINE[0]
ADMINSERVER_LISTEN_ON_ALL_INTERFACES = false

CLUSTER = '<%= @cluster %>'
MULTICAST_ADDRESS = '239.192.0.0'
MULTICAST_PORT = '2300'
FRONTEND_HOST = '<%= @admin_server_listen_address %>'
FRONTEND_HTTP_PORT = '80'
FRONTEND_HTTPS_PORT = '443'
CLUSTER_ADDRESS = ""

MACHINES = <%= @machines %>
MANAGED_SERVER_MACHINES = <%= @ms_machines %>
MANAGED_SERVER_PORTS    = <%= @ms_ports %>
MANAGED_SERVER_ARGUMENT = '<%= @ms_args %>'

DOMAIN_PASSWORD = '<%= @admin_password %>'
NODEMANAGER_USERNAME = '<%= @nm_user %>'
NODEMANAGER_PASSWORD = '<%= @nm_password %>'
NODEMANAGER_LISTEN_PORT = '<%= @nm_port %>'
NODEMANAGER_SECURE_LISTENER = true

LOG_DIR = '<%= @log_dir %>'

REPOS_DBURL = '<%= @rcu_jdbc_url %>'
REPOS_DBUSER_PREFIX = '<%= @rcu_prefix %>'
REPOS_DBPASSWORD = '<%= @rcu_password %>'

DEVELOPMENT_MODE = false
APP_PATH = '<%= @applications_dir %>'

ADM_JAVA_ARGUMENTS = '<%= @admin_args %>'

DOM = '<%= @dom %>'

#------------------------------- READ BASIC TEMPLATE --------------------------------#
print('Start normal domain... with template <%= @wl_template %> ')
readTemplate('<%= @wl_template %>')

print('Set crossdomain')
set_cross_domain()

#---------------------------------- SET DOMAIN LOG ----------------------------------#
print('Set domain log')
change_log('domain', DOMAIN, LOG_DIR + '/' + ADMIN_SERVER)

#------------------------ CREATE ADMIN AND MS MACHINES ------------------------------#
for i in range(len(MACHINES)):
    create_machine(MACHINES[i], MACHINES[i]+'.'+DOM, NODEMANAGER_LISTEN_PORT, NODEMANAGER_SECURE_LISTENER)

#--------------------------------- CREATE ADMIN SERVER ----------------------------------#
if ADMINSERVER_LISTEN_ON_ALL_INTERFACES:
    change_admin_server(ADMIN_SERVER, MANAGED_SERVER_MACHINES[i], None, ADMIN_SERVER_LISTEN_PORT, ADM_JAVA_ARGUMENTS, JAVA_HOME)
else:
    change_admin_server(ADMIN_SERVER, ADMIN_MACHINE, ADMIN_SERVER_LISTEN_ADDRESS, ADMIN_SERVER_LISTEN_PORT, ADM_JAVA_ARGUMENTS, JAVA_HOME)
change_log('server', ADMIN_SERVER, LOG_DIR + '/' + ADMIN_SERVER)
change_ssl_with_port(ADMIN_SERVER, JSSE_ENABLED, int(ADMIN_SERVER_LISTEN_PORT) + 1)

#-------------------------------- CREATE MANAGED SERVERS ----------------------------------#
for i in range(len(MANAGED_SERVER_MACHINES)):
     cd('/')
     server = DOMAIN+'_ms0'+str(i+1)
     create(server, 'Server')

#------------------------------ CHANGE MANAGED SERVERS ------------------------------------#
for i in range(len(MANAGED_SERVER_MACHINES)):
     server = DOMAIN+'_ms0'+str(i+1)
     change_managed_server(server, MANAGED_SERVER_MACHINES[i], MANAGED_SERVER_MACHINES[i]+'.'+DOM, MANAGED_SERVER_PORTS[i], MANAGED_SERVER_ARGUMENT, JAVA_HOME)
     change_ssl_with_port(server, JSSE_ENABLED, int(MANAGED_SERVER_PORTS[i]) + 1)
     change_log('server', server, LOG_DIR + '/' + server)

#----------------------------- CREATE CLUSTER AND ASSIGN SERVERS ---------------------------#
cd('/')
create(CLUSTER, 'Cluster')
for i in range(len(MANAGED_SERVER_MACHINES)):
     server = DOMAIN+'_ms0'+str(i+1)
     host = MANAGED_SERVER_MACHINES[i] +'.' + DOM
     print "cluster " + CLUSTER + " member " + server
     cd('/')
     assign('Server',server,'Cluster',CLUSTER)
     cd('/Cluster/' + CLUSTER)
     CLUSTER_ADDRESS = CLUSTER_ADDRESS + host + ':' + MANAGED_SERVER_PORTS[i] + ','

cd('/Cluster/' + CLUSTER)
set('MulticastAddress', MULTICAST_ADDRESS)
set('MulticastPort', int(MULTICAST_PORT))
set('FrontendHost', FRONTEND_HOST)
set('FrontendHTTPPort', int(FRONTEND_HTTP_PORT))
set('FrontendHTTPSPort', int(FRONTEND_HTTPS_PORT))
CLUSTER_ADDRESS = CLUSTER_ADDRESS[:-1]
print CLUSTER_ADDRESS
cmo.setClusterAddress(CLUSTER_ADDRESS)


#------------------------------ SET WEBLOGIC PASSWORD --------------------------------------#
print('Set password...')
set_weblogic_password(ADMIN_USER, ADMIN_PASSWORD)

#------------------------------ SET DOMAIN OPTIONS -----------------------------------------#
if DEVELOPMENT_MODE == True:
    setOption('ServerStartMode', 'dev')
else:
    setOption('ServerStartMode', 'prod')

setOption('JavaHome', JAVA_HOME)

#--------------------------- WRITE AND CLOSE DOMAIN TEMPLATE -------------------------------#
writeDomain(DOMAIN_PATH)
closeTemplate()

readDomain(DOMAIN_PATH)
setOption('AppDir', APP_PATH)

#print 'Adding EM Template'
#addTemplate(MW_HOME+'/em/common/templates/wls/oracle.em_wls_template.jar')

dumpStack()

print 'Extend...soa domain with template SOA jar'
#addTemplate(MW_HOME+'/oracle_common/common/templates/wls/oracle.wls-webservice-template.jar')
addTemplate('<%= @middleware_home_dir %>/soa/common/templates/wls/oracle.soa_template.jar')
#---------------------------------- CHANGE DATASOURCE ---------------------------------------#
print 'Change datasource mds-owsm'
change_datasource('mds-owsm', REPOS_DBUSER_PREFIX + '_MDS', REPOS_DBPASSWORD, REPOS_DBURL)

print 'Change datasource LocalScvTblDataSource for service table'
change_datasource('LocalSvcTblDataSource', REPOS_DBUSER_PREFIX + '_STB', REPOS_DBPASSWORD, REPOS_DBURL)

print 'Call getDatabaseDefaults which reads the service table'
getDatabaseDefaults()

change_datasource_to_xa('SOADataSource')

print 'end datasources'

#--------------------------------------- ADD SERVERS TO SERVER GROUPS ---------------------------------#

adminServerGroup = ["WSM-CACHE-SVR" , "WSMPM-MAN-SVR" , "JRF-MAN-SVR"]
setServerGroups(ADMIN_SERVER, adminServerGroup)

serverGroup = ["SOA-MGD-SVRS"]
print 'Add server group SOA-MGD-SVRS to cluster'
for i in range(len(MANAGED_SERVER_MACHINES)):
    server = DOMAIN+'_ms0'+str(i+1)
    cd('/')
    setServerGroups(server, serverGroup)
print 'end server groups'

#-------------------------------------- DELETE DEFAULST SERVER ----------------------------------------#
if CLUSTER:
    soaServers = getClusterServers(CLUSTER, ADMIN_SERVER)
    if 'soa_server1' in soaServers:
      pass
    else:
      print "delete soa_server1"
      cd('/')
      ls()
      delete('soa_server1', 'Server')
      ls()

cd('/SecurityConfiguration/' + DOMAIN)
cmo.setNodeManagerUsername(NODEMANAGER_USERNAME)
cmo.setNodeManagerPasswordEncrypted(NODEMANAGER_PASSWORD)

dumpStack()
updateDomain()
closeDomain()

#-------------------------------- CREATE BOOT.PROPS FOR DOMAIN ---------------------------------#
create_admin_startup_properties_file(DOMAIN_PATH + '/servers/' + ADMIN_SERVER + '/data/nodemanager', ADM_JAVA_ARGUMENTS)
create_boot_properties_file(DOMAIN_PATH + '/servers/' + ADMIN_SERVER + '/security', 'boot.properties', ADMIN_USER, ADMIN_PASSWORD)
create_boot_properties_file(DOMAIN_PATH + '/config/nodemanager', 'nm_password.properties', ADMIN_USER, ADMIN_PASSWORD)

print 'Exiting...'
exit()
