from enum import Enum


class JailParameter(Enum):
    PATH = 'path'
    IP4_ADDR = 'ip4.addr'
    IP4_SADDR_SEL = 'ip4.saddrsel'
    IP4 = 'ip4'
    IP6_ADDR = 'ip6.addr'
    IP6_SADDR_SEL = 'ip6.saddrsel'
    IP6 = 'ip6'
    VNET = 'vnet'
    HOSTNAME = 'host.hostname'
    HOST = 'host'
    SECURELEVEL = 'securelevel'
    DEVFS_RULESET = 'devfs_ruleset'
    CHILDREN_MAX = 'children.max'
    CHILDREN_CUR = 'children.cur'
    ENFORCE_STATFS = 'enforce_statfs'
    PERSIST = 'persist'
    CPUSET_ID = 'cpuset.id'
    DYING = 'dying'
    PARENT = 'parent'
    OS_RELEASE = 'osrelease'
    OS_REL_DATE = 'osreldate'
    ALLOW_SET_HOSTNAME = 'allow.set_hostname'
    ALLOW_SYSVIPC = 'allow.sysvipc'
    ALLOW_RAW_SOCKETS = 'allow.raw_sockets'
    ALLOW_CHFLAGS = 'allow.chflags'
    ALLOW_MOUNT = 'allow.mount'
    ALLOW_MOUNT_DEVFS = 'allow.mount.devfs'
    ALLOW_QUOTAS = 'allow.quotas'
    ALLOW_READ_MSGBUF = 'allow.read_msgbuf'
    ALLOW_SOCKET_AF = 'allow.socket_af'
    ALLOW_MLOCK = 'allow.mlock'
    ALLOW_RESERVED_PORTS = 'allow.reserved_ports'
    ALLOW_MOUNT_FDESCFS = 'allow.mount.fdescfs'
    ALLOW_MOUNT_FUSEFS = 'allow.mount.fusefs'
    ALLOW_MOUNT_NULLFS = 'allow.mount.nullfs'
    ALLOW_MOUNT_PROCFS = 'allow.mount.procfs'
    ALLOW_MOUNT_LINPROCFS = 'allow.mount.linprocfs'
    ALLOW_MOUNT_LINSYSFS = 'allow.mount.linsysfs'
    ALLOW_MOUNT_TMPFS = 'allow.mount.tmpfs'
    ALLOW_MOUNT_ZFS = 'allow.mount.zfs'
    ALLOW_VMM = 'allow.vmm'
    LINUX = 'linux'
    LINUX_OSNAME = 'linux.osname'
    LINUX_OSRELEASE = 'linux.osrelease'
    LINUX_OSS_VERSION = 'linux.oss_version'
    SYSVMSG = 'sysvmsg'
    SYSVSEM = 'sysvsem'
    SYSVSHM = 'sysvshm'
    EXEC_PRESTART = 'exec.prestart'
    EXEC_CREATED = 'exec.created'
    EXEC_START = 'exec.start'
    COMMAND = 'command'
    EXEC_POSTSTART = 'exec.poststart'
    EXEC_PRESTOP = 'exec.prestop'
    EXEC_STOP = 'exec.stop'
    EXEC_POSTSTOP = 'exec.poststop'
    EXEC_CLEAN = 'exec.clean'
    EXEC_JAIL_USER = 'exec.jail_user'
    EXEC_SYSTEM_JAIL_USER = 'exec.system_jail_user'
    EXEC_SYSTEM_USER = 'exec.system_user'
    EXEC_TIMEOUT = 'exec.timeout'
    EXEC_CONSOLELOG = 'exec.consolelog'
    EXEC_FIB = 'exec.fib'
    STOP_TIMEOUT = 'stop.timeout'
    INTERFACE = 'interface'
    VNET_INTERFACE = 'vnet.interface'
    IP_HOSTNAME = 'ip_hostname'
    MOUNT = 'mount'
    MOUNT_FSTAB = 'mount.fstab'
    MOUNT_DEVFS = 'mount.devfs'
    MOUNT_FDESCFS = 'mount.fdescfs'
    MOUNT_PROCFS = 'mount.procfs'
    ALLOW_DYING = 'allow.dying'
    DEPEND = 'depend'