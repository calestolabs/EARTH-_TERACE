import {Globe2} from 'lucide-react';
import styles from './EarthtraceLogo.module.css';
/** Matches the original Home logo, isolated from Member 03/04 typography. */
export default function EarthtraceLogo(){
 return <a className={styles.logo} href="/" aria-label="EARTHTRACE home">
  <span className={styles.symbol} aria-hidden="true"><Globe2 size={24}/></span>
  <span>EARTH<span className={styles.trace}>TRACE</span><small className={styles.tagline}>EVERY CHANGE LEAVES A CLUE</small></span>
 </a>;
}
