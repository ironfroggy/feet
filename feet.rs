use std::env;
use std::ffi::OsString;
use std::fs;
use std::io;
use std::io::{Error, Write, stdout};
use std::path::Path;
use std::process::{Command, Stdio};


fn get_exec_stem() -> OsString {
    let current_exe = std::env::current_exe().expect("cannot get current process name");
    let path = Path::new(&current_exe);
    let stem = path.file_stem().expect("cannot get file stem");
    return stem.to_owned();
}


fn extract_runtime(exec_name: OsString, data_dir: OsString) -> Result<(), Error> {
    println!("Extracting the Python Feet Runtime... (one-time operation)");

    let file = fs::File::open(&exec_name).unwrap();
    let mut archive = zip::ZipArchive::new(file).unwrap();
    let total = archive.len();
    
    for i in 0..total {
        let mut file = archive.by_index(i).unwrap();
        let outpath = file.sanitized_name();

        if (&*file.name()).ends_with('/') {
            fs::create_dir_all(&outpath).unwrap();
        } else {
            if i % 100 == 0 && i != 0 {
                println!(" {}% ", ((i as f64 / total as f64) * 100.0) as i32);
            } else if i != 0 {
                print!(".");
                stdout().flush()?;
            }
            if let Some(p) = outpath.parent() {
                if !p.exists() {
                    fs::create_dir_all(&p).unwrap();
                }
            }
            let mut outfile = fs::File::create(&outpath).unwrap();
            io::copy(&mut file, &mut outfile).unwrap();
        }

        // Get and Set permissions
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;

            if let Some(mode) = file.unix_mode() {
                fs::set_permissions(&outpath, fs::Permissions::from_mode(mode)).unwrap();
            }
        }
    }
    std::fs::rename("feet", &data_dir)?;
    println!(" done!");
    Ok(())
}


fn main() -> Result<(), Error> {
    let exec = std::env::current_exe()?;
    let exec_path = Path::new(&exec);
    let exec_name = exec_path.file_name().unwrap();
    let exec_base = get_exec_stem();
    let data_dir = format!("{}_data", exec_base.to_str().unwrap());

    let mut args: Vec<String> = env::args().collect();
    args.remove(0);

    // Is there a sub-command? most are implemented in the python utility, but check if we
    // need to process one.
    if args.len() > 0 {
        match args[0].as_ref() {

            // the "clean" command is implemented here, because the unpacked Python
            // can't delete itself
            "clean" => {
                fs::remove_dir_all(Path::new(&data_dir))?;
                std::process::exit(0);
            },
            _ => {
                
            },
        }
    }

    // Make sure we don't run inside the feet repo, only in test places.
    if Path::new("./feetmaker.py").exists() {
        println!("Do not run {:?} in its own source directory", exec_name);
        std::process::exit(1);
    }

    // If a pre-existing extracted runtime directory exists, clear it if
    // it is older than this executable
    if Path::new(&data_dir).exists() {
        let mod_exec = Path::new(&exec_name).metadata()?.modified()?;
        let mod_runtime = Path::new(&data_dir).metadata()?.modified()?;

        if mod_exec > mod_runtime {
            fs::remove_dir_all(Path::new(&data_dir))?;
        }
    }

    // If there is no runtime directory, either because this is a first-run
    // or the directory was cleared for a new version, extract the whole thing
    if !Path::new(&data_dir).exists() {
        match extract_runtime(exec_name.to_owned(), OsString::from(data_dir.to_owned())) {
            Ok(()) => (),
            Err(err) => panic!(err)
        }
    }

    // Next, if there is a requirements file, install that
    if Path::new("./requirements.txt").exists() && !Path::new(&data_dir).join("requirements_installed.txt").exists() {
        let script = &format!("{}/feet.py", data_dir);
        println!("Installing requirements... {}", script);
        let mut child = Command::new(format!("{}/cpython/python", data_dir))
            .args(&[script, "library", "--update"])
            .stderr(Stdio::inherit())
            .stdout(Stdio::inherit())
            .stdin(Stdio::inherit())
            .spawn()?;
        child.wait().expect("Invoking the Feet runtime script failed.");
        let _f = fs::File::create(Path::new(&data_dir).join("requirements_installed.txt"))?;
    }

    // Now, runtime is either extracted or already was, so run the commands

    // println!("{}/feet.py", data_dir);
    let mut child = Command::new(format!("{}/cpython/python", data_dir))
        .arg(format!("{}/feet.py", data_dir))
        .args(args)
        .stderr(Stdio::inherit())
        .stdout(Stdio::inherit())
        .stdin(Stdio::inherit())
        .spawn()?;

    let status = child.wait().expect("Invoking the Feet runtime script failed.");
    match status.code() {
        Some(code) => std::process::exit(code),
        None       => {
            println!("Process terminated by signal");
            std::process::exit(255);
        },
    }
}
