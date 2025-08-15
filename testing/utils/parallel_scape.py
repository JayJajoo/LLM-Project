from playwright.async_api import async_playwright
import asyncio
import json
import os
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from functools import partial
import time


async def extract_prereq_table(page):
    def table_to_string(table_data):
        parts = []
        for row in table_data:
            row_str = " ".join(cell.strip() for cell in row if cell.strip())
            if row_str:
                parts.append(row_str)
        return " ".join(parts)

    table_locator = page.locator("table.basePreqTable")
    await asyncio.sleep(1)
    if await table_locator.count() == 0:
        return "None"

    rows = await table_locator.locator("tbody tr").all()
    # print(f"Found {len(rows)} prerequisite rows")

    all_data = []
    for row in rows:
        cells = await row.locator("td").all()
        row_data = [await cell.inner_text() for cell in cells]
        all_data.append(row_data)
    
    return table_to_string(all_data)


async def setup_browser_and_navigate(college):
    """Setup browser and navigate to the search results page"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Use headless for parallel processing
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://nubanner.neu.edu/StudentRegistrationSsb/ssb/registration")
        await page.get_by_text(text="Browse Course Catalog").click()
        await page.click("#select2-chosen-1")
        await page.wait_for_selector("input#s2id_autogen1_search", state="attached")
        await page.type("input#s2id_autogen1_search", text="Fall 2025 Semester", delay=0)
        await page.get_by_text("Fall 2025 Semester").click()
        await page.get_by_role(role="button", name="Continue").click()
        
        await page.wait_for_selector(selector="a#advanced-search-link")
        await page.click(selector="a#advanced-search-link")

        await page.wait_for_selector("input#s2id_autogen4")
        await page.click("input#s2id_autogen4")
        await page.type("input#s2id_autogen4", text="Graduate", delay=0)
        await page.locator("div.select2-result-label", has_text="Graduate").nth(3).click()

        await page.click("div#s2id_txt_college input.select2-input")
        await page.fill("div#s2id_txt_college input.select2-input", f"{college}")
        await page.wait_for_timeout(500)
        await page.click(f"div.select2-result-label:has-text('{college}')")

        await page.click("button#search-go")
        
        await page.wait_for_selector("div.grid-main-wrapper")
        await page.wait_for_selector("table#table1")
        await asyncio.sleep(3)
        
        # Get total pages
        total_pages_text = await page.locator("span.paging-text.total-pages").inner_text()
        total_pages = int(total_pages_text.strip())
        
        await browser.close()
        return total_pages


async def process_course_on_page(page, data_id):
    """Process a single course and return its data"""
    try:
        course_number = await page.locator(f'tr[data-id="{data_id}"] td[data-property="courseNumber"]').inner_text()
        
        selector = f'tr[data-id="{data_id}"] a.course-details-link'
        await page.wait_for_selector(selector, state="visible", timeout=15000)
        await page.click(selector)

        await page.wait_for_selector("div#courseDetailsWrapper")

        title = await page.locator("section[aria-labelledby='catalog'] span#courseTitle").inner_text()
        college = await page.locator("section[aria-labelledby='catalog'] span.status-bold:has-text('College:') + span").inner_text()
        department = await page.locator("section[aria-labelledby='catalog'] span.status-bold:has-text('Department:') + span").inner_text()
        credit_hours = await page.locator("section[aria-labelledby='catalog'] span.credit-hours-direction").first.inner_text()

        await page.get_by_role("link", name="Course Description").first.click()
        description = await page.locator("section[aria-labelledby='courseDescription']").inner_text()

        await page.get_by_role("link", name="Prerequisites").click()
        prerequisites = await extract_prereq_table(page=page)

        course_data = {
            "data_id": data_id,
            "course_number": course_number,
            "title": title.strip(),
            "college": college.strip(),
            "department": department.strip(),
            "credit_hours": credit_hours.strip(),
            "description": description.strip(),
            "prerequisites": prerequisites.strip()
        }

        # Close the dialog
        close_btn = page.locator("button.primary-button.small-button", has_text="Close")
        await close_btn.wait_for(state="visible")
        await close_btn.click()
        await asyncio.sleep(1)  # Brief pause between courses
        
        return course_data
    except Exception as e:
        print(f"Error processing course {data_id}: {e}")
        return None


async def process_page_range(page_start, page_end, college, worker_id=0):
    """Process a range of pages in a single browser instance"""
    print(f"Worker {worker_id}: Processing pages {page_start} to {page_end}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Setup and navigate (same as before)
        await page.goto("https://nubanner.neu.edu/StudentRegistrationSsb/ssb/registration")
        await page.get_by_text(text="Browse Course Catalog").click()
        await page.click("#select2-chosen-1")
        await page.wait_for_selector("input#s2id_autogen1_search", state="attached")
        await page.type("input#s2id_autogen1_search", text="Fall 2025 Semester", delay=0)
        await page.get_by_text("Fall 2025 Semester").click()
        await page.get_by_role(role="button", name="Continue").click()
        
        await page.wait_for_selector(selector="a#advanced-search-link")
        await page.click(selector="a#advanced-search-link")

        await page.wait_for_selector("input#s2id_autogen4")
        await page.click("input#s2id_autogen4")
        await page.type("input#s2id_autogen4", text="Graduate", delay=0)
        await page.locator("div.select2-result-label", has_text="Graduate").nth(3).click()

        await page.click("div#s2id_txt_college input.select2-input")
        await page.fill("div#s2id_txt_college input.select2-input", f"{college}")
        await page.wait_for_timeout(500)
        await page.click(f"div.select2-result-label:has-text('{college}')")

        await page.click("button#search-go")
        
        await page.wait_for_selector("div.grid-main-wrapper")
        await page.wait_for_selector("table#table1")
        await asyncio.sleep(3)
        
        # Navigate to start page if not page 1
        if page_start > 1:
            page_number_input = page.locator("input.page-number.enabled")
            await page_number_input.fill(str(page_start))
            await page_number_input.press("Enter")
            await asyncio.sleep(3)
        
        worker_data = []
        current_page = page_start
        
        while current_page <= page_end:
            print(f"Worker {worker_id}: Processing page {current_page}")
            
            await page.wait_for_selector("div.grid-main-wrapper")
            await page.wait_for_selector("table#table1")
            await asyncio.sleep(2)

            # Get all course data-ids on current page
            rows = await page.query_selector_all("tr")
            data_ids = [await row.get_attribute("data-id") for row in rows][1:]
            
            # Process courses sequentially within the page (to avoid UI conflicts)
            page_courses = []
            for data_id in data_ids:
                if data_id:  # Skip empty data_ids
                    course_data = await process_course_on_page(page, data_id)
                    if course_data:
                        page_courses.append(course_data)
            
            worker_data.extend(page_courses)
            print(f"Worker {worker_id}: Completed page {current_page} with {len(page_courses)} courses")
            
            # Move to next page
            current_page += 1
            if current_page <= page_end:
                page_number_input = page.locator("input.page-number.enabled")
                await page_number_input.fill(str(current_page))
                await page_number_input.press("Enter")
                await asyncio.sleep(3)
        
        await browser.close()
        print(f"Worker {worker_id}: Completed processing {len(worker_data)} courses")
        return worker_data


def run_worker(page_start, page_end, college, worker_id):
    """Wrapper function to run async process_page_range in a separate process"""
    return asyncio.run(process_page_range(page_start, page_end, college, worker_id))


#College of Engineering
#Coll of Professional Studies
#Khoury Coll of Comp Sciences
#College of Science

#Bouve College of Hlth Sciences
#Coll of Arts, Media & Design
#Coll of Soc Sci & Humanities
#D'Amore-McKim School Business
#Office of Provost
#School of Law

async def main():
    college = "Coll of Professional Studies"
    
    # Get total pages first
    print("Getting total pages...")
    total_pages = await setup_browser_and_navigate(college)
    print(f"Total pages to process: {total_pages}")
    
    # Determine number of workers (adjust based on your system)
    num_workers = min(multiprocessing.cpu_count(), 6)  # Limit to 4 to avoid overwhelming the server
    pages_per_worker = max(1, total_pages // num_workers)
    
    print(f"Using {num_workers} workers, approximately {pages_per_worker} pages per worker")
    
    # Create page ranges for each worker
    worker_ranges = []
    for i in range(num_workers):
        start_page = i * pages_per_worker + 1
        end_page = min((i + 1) * pages_per_worker, total_pages)
        if start_page <= total_pages:
            worker_ranges.append((start_page, end_page, college, i))
    
    # Adjust last worker to cover remaining pages
    if worker_ranges and worker_ranges[-1][1] < total_pages:
        worker_ranges[-1] = (worker_ranges[-1][0], total_pages, college, worker_ranges[-1][3])
    
    print(f"Worker ranges: {worker_ranges}")
    
    # Process pages in parallel using multiprocessing
    start_time = time.time()
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(run_worker, *worker_range) for worker_range in worker_ranges]
        
        # Collect results
        all_results = []
        for i, future in enumerate(futures):
            try:
                result = future.result()
                all_results.extend(result)
                print(f"Worker {i} completed successfully with {len(result)} courses")
            except Exception as e:
                print(f"Worker {i} failed with error: {e}")
    
    end_time = time.time()
    print(f"Total processing time: {end_time - start_time:.2f} seconds")
    print(f"Total courses processed: {len(all_results)}")
    
    # Save results
    BASE_PATH = os.getcwd()
    output_file = f"{BASE_PATH}/courses_{college.replace(' ', '_')}_parallel.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    asyncio.run(main())

