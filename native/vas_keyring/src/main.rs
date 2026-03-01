use keyring::Entry;
use std::env;

fn usage() {
    eprintln!("usage: vas_keyring <set|get|delete> <service> <account> [--from-env]");
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 4 {
        usage();
        std::process::exit(2);
    }

    let cmd = &args[1];
    let service = &args[2];
    let account = &args[3];
    let entry = Entry::new(service, account).expect("invalid keyring params");

    match cmd.as_str() {
        "set" => {
            if args.len() < 4 || args.len() > 5 {
                usage();
                std::process::exit(2);
            }
            let secret = if args.len() == 5 && args[4] != "--from-env" {
                if env::var("VAS_ALLOW_INSECURE_KEYRING_ARG").ok().as_deref() == Some("1") {
                    args[4].clone()
                } else {
                    eprintln!("keyring_set_failed:insecure_cli_secret_disallowed");
                    std::process::exit(2);
                }
            } else {
                match env::var("VAS_KEYRING_SECRET") {
                    Ok(v) => v,
                    Err(_) => {
                        eprintln!("keyring_set_failed:missing_secret");
                        std::process::exit(2);
                    }
                }
            };
            if secret.is_empty() {
                eprintln!("keyring_set_failed:empty_secret");
                std::process::exit(2);
            }
            if let Err(err) = entry.set_password(&secret) {
                eprintln!("keyring_set_failed:{err}");
                std::process::exit(1);
            }
            println!("ok");
        }
        "get" => match entry.get_password() {
            Ok(secret) => println!("{secret}"),
            Err(err) => {
                eprintln!("keyring_get_failed:{err}");
                std::process::exit(1);
            }
        },
        "delete" => {
            if let Err(err) = entry.delete_credential() {
                eprintln!("keyring_delete_failed:{err}");
                std::process::exit(1);
            }
            println!("ok");
        }
        _ => {
            usage();
            std::process::exit(2);
        }
    }
}
