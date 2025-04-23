# Browser Automation Best Practices

## DOM Exploration
- Always thoroughly explore DOM structure before interacting with elements
- Use sufficient `max_depth` values (minimum 8-10) to see nested elements
- When first navigating to a site, inspect its structure before assuming selectors
- Verify element existence before waiting or interacting with them

## Element Selection
- Create robust selectors that won't break with minor page changes
- Use multiple identification methods when possible (class, id, text content, etc.)
- Verify selectors work before using them in subsequent operations
- When a selector fails, explore the DOM again to understand what changed

## Page Interaction
- Wait for page to fully load before performing actions
- Use proper error handling when elements aren't found
- Don't assume all pages have the same structure, even within the same site
- Verify action success before moving to next steps

## Search Strategy
1. First navigate to the site
2. Thoroughly explore DOM to understand structure (`max_depth` ≥ 10)
3. Identify form inputs and submit buttons
4. Perform the search action
5. Verify search results loaded properly before extracting them
6. Use JavaScript execution when direct element interaction is difficult

## Common Mistakes to Avoid
- Using selectors without verifying they exist
- Shallow DOM exploration that misses important elements
- Waiting for elements that don't exist in the page
- Not adapting to different site layouts and behaviors
- Using trial-and-error instead of systematic exploration
- Not checking if actions succeeded before proceeding

## Debugging Tips
- Use `execute_js` to verify elements exist: `document.querySelector('selector') !== null`
- Print full DOM when having trouble finding elements
- Check console logs for JavaScript errors that might affect page behavior
- Use step-by-step verification rather than assuming success 